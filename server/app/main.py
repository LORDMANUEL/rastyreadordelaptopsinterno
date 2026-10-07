import asyncio
import hashlib
import logging
import os
import secrets
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .rbac import (
    ROLE_ADMIN,
    ROLE_AUDIT,
    ROLE_SUPPORT,
    SESSION_SECRET,
    SESSION_TTL_SECONDS,
    SessionIdentity,
    create_session,
    parse_session,
    verify_auth_value,
)
from .auth_schemas import LoginRequest
from .database import SessionLocal, engine
from .http_security import guard_request
from .models import AuditEvent, Device, DeviceObservation
from .enrollment_models import EnrollmentCode
from .software_models import InstalledApplication
from .software_policy_models import DeviceSoftwareAssignment, SoftwareCatalogItem
from .software_task_models import DeviceSoftwareTask
from .network_geo import NetworkLocation, lookup_network_location, validate_geo_configuration
from .user_models import UserAccount
from .schemas import DeviceAuthRevoke, DeviceUpdate, EnrollRequest, EnrollResponse, HeartbeatRequest, LostModeUpdate
from .enrollment_schemas import EnrollmentCodeCreate, EnrollmentCodeRevoke
from .software_schemas import SoftwareInventorySync
from .software_policy_schemas import DeviceSoftwareAssignmentCreate, SoftwareCatalogCreate, SoftwareCatalogUpdate
from .software_task_schemas import SoftwareTaskCreate, SoftwareTaskResult

APP_NAME = "YUDE Asset Guard"
ENROLLMENT_TOKEN = os.getenv("ENROLLMENT_TOKEN", "")
ALLOW_LEGACY_ENROLLMENT_TOKEN = os.getenv("ALLOW_LEGACY_ENROLLMENT_TOKEN", "false").lower() in {"1", "true", "yes", "on"}
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
HEARTBEAT_SECONDS = int(os.getenv("HEARTBEAT_SECONDS", "300"))
OFFLINE_SECONDS = int(os.getenv("HEARTBEAT_OFFLINE_SECONDS", "600"))
DEVICE_AUTH_ROTATE_DAYS = int(os.getenv("DEVICE_AUTH_ROTATE_DAYS", "7"))
DEVICE_AUTH_TTL_DAYS = int(os.getenv("DEVICE_AUTH_TTL_DAYS", "45"))
OFFLINE_MONITOR_SECONDS = int(os.getenv("OFFLINE_MONITOR_SECONDS", "60"))
STATIC_DIR = Path(__file__).parent / "static"
LOGGER = logging.getLogger("yude_asset_guard")

def validate_configuration() -> None:
    required = {
        "ADMIN_TOKEN": ADMIN_TOKEN,
    }
    if ALLOW_LEGACY_ENROLLMENT_TOKEN:
        required["ENROLLMENT_TOKEN"] = ENROLLMENT_TOKEN
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError("missing required configuration: " + ", ".join(missing))
    validate_geo_configuration()


def scan_offline_devices(db: Session, now: datetime | None = None) -> int:
    current = now or datetime.now(timezone.utc)
    marked = 0
    devices = db.scalars(
        select(Device).where(Device.offline_since.is_(None))
    ).all()
    for device in devices:
        age = current - as_utc(device.last_seen)
        if age.total_seconds() <= OFFLINE_SECONDS:
            continue
        device.offline_since = current
        db.add(AuditEvent(
            event_type="DEVICE_OFFLINE",
            device_id=device.id,
            actor="system",
            detail=f"last_seen={as_utc(device.last_seen).isoformat()}",
        ))
        marked += 1
    if marked:
        db.commit()
    return marked


async def offline_monitor_loop() -> None:
    while True:
        try:
            with SessionLocal() as db:
                scan_offline_devices(db)
        except Exception:
            LOGGER.exception("offline monitor failed")
        await asyncio.sleep(max(15, OFFLINE_MONITOR_SECONDS))


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_configuration()
    task = asyncio.create_task(offline_monitor_loop())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title=APP_NAME, version="0.13.0", lifespan=lifespan)
app.middleware("http")(guard_request)


def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def issue_device_auth(device: Device, now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc)
    raw = secrets.token_urlsafe(48)
    device.token_hash = sha256(raw)
    device.auth_issued_at = current
    device.auth_expires_at = current + timedelta(days=DEVICE_AUTH_TTL_DAYS)
    device.auth_revoked_at = None
    device.auth_generation = max(1, int(device.auth_generation or 0) + 1)
    return raw


def should_rotate_device_auth(device: Device, now: datetime | None = None) -> bool:
    current = now or datetime.now(timezone.utc)
    if device.auth_issued_at is None:
        return True
    issued = as_utc(device.auth_issued_at)
    return current - issued >= timedelta(days=DEVICE_AUTH_ROTATE_DAYS)


def apply_network_location(
    device: Device,
    location: NetworkLocation | None,
    now: datetime | None = None,
) -> None:
    if location is None:
        return
    device.geo_country_code = location.country_code
    device.geo_country_name = location.country_name
    device.geo_region_name = location.region_name
    device.geo_city_name = location.city_name
    device.geo_accuracy_km = location.accuracy_km
    device.geo_updated_at = now or datetime.now(timezone.utc)


def require_identity(
    request: Request,
    x_admin_token: str = Header(default=""),
    assetguard_session: str | None = Cookie(default=None),
    db: Session = Depends(db_session),
) -> SessionIdentity:
    if x_admin_token and secrets.compare_digest(x_admin_token, ADMIN_TOKEN):
        return SessionIdentity(username="automation", role=ROLE_ADMIN)

    if assetguard_session:
        identity = parse_session(assetguard_session)
        if identity is not None:
            account = db.scalar(select(UserAccount).where(UserAccount.username == identity.username))
            if account is not None and account.is_active and account.role == identity.role:
                return identity

    raise HTTPException(status_code=401, detail="authentication required")


def require_roles(*allowed_roles: str):
    def dependency(identity: SessionIdentity = Depends(require_identity)) -> SessionIdentity:
        if identity.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="insufficient permissions")
        return identity

    return dependency


def device_from_auth(
    authorization: str = Header(default=""),
    db: Session = Depends(db_session),
) -> Device:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    raw = authorization.removeprefix("Bearer ").strip()
    device = db.scalar(select(Device).where(Device.token_hash == sha256(raw)))
    if device is None:
        raise HTTPException(status_code=401, detail="invalid device token")

    now = datetime.now(timezone.utc)
    if device.auth_revoked_at is not None:
        raise HTTPException(status_code=401, detail="device credential revoked")
    if device.auth_expires_at is not None and as_utc(device.auth_expires_at) <= now:
        raise HTTPException(status_code=401, detail="device credential expired")

    return device


def client_ip(request: Request) -> str | None:
    # Uvicorn's trusted proxy middleware normalizes request.client.
    # Do not trust a raw X-Forwarded-For header from arbitrary clients here.
    return request.client.host if request.client else None


def software_app_key(name: str, version: str | None, publisher: str | None, source: str | None) -> str:
    canonical = "|".join(
        (value or "").strip().lower()
        for value in (name, version, publisher, source)
    )
    return sha256(canonical)


def consume_enrollment_code(
    raw_value: str,
    platform: str,
    db: Session,
) -> EnrollmentCode | None:
    now = datetime.now(timezone.utc)
    code = db.scalar(
        select(EnrollmentCode).where(EnrollmentCode.code_hash == sha256(raw_value))
    )
    if code is not None:
        if code.revoked_at is not None:
            raise HTTPException(status_code=403, detail="enrollment code revoked")
        if as_utc(code.expires_at) <= now:
            raise HTTPException(status_code=403, detail="enrollment code expired")
        if code.use_count >= code.max_uses:
            raise HTTPException(status_code=403, detail="enrollment code exhausted")
        if code.platform and code.platform.lower() != platform.lower():
            raise HTTPException(status_code=403, detail="enrollment code platform mismatch")

        code.use_count += 1
        code.last_used_at = now
        return code

    if (
        ALLOW_LEGACY_ENROLLMENT_TOKEN
        and ENROLLMENT_TOKEN
        and secrets.compare_digest(raw_value, ENROLLMENT_TOKEN)
    ):
        return None

    raise HTTPException(status_code=403, detail="invalid enrollment code")


@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME, "version": app.version}


@app.get("/ready")
def ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ready", "database": "ok"}


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/api/v1/auth/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(db_session)):
    if not SESSION_SECRET:
        raise HTTPException(status_code=503, detail="web authentication is not configured")

    account = db.scalar(select(UserAccount).where(UserAccount.username == payload.username))
    if (
        account is None
        or not account.is_active
        or not verify_auth_value(payload.password, account.auth_salt, account.auth_digest)
    ):
        raise HTTPException(status_code=401, detail="invalid credentials")

    account.last_login = datetime.now(timezone.utc)
    account.updated_at = datetime.now(timezone.utc)
    db.add(AuditEvent(event_type="USER_LOGIN", actor=account.username, detail=account.role))
    db.commit()

    response.set_cookie(
        key="assetguard_session",
        value=create_session(account.username, account.role),
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
        max_age=SESSION_TTL_SECONDS,
    )
    return {"ok": True, "username": account.username, "role": account.role}


@app.post("/api/v1/auth/logout")
def logout(response: Response):
    response.delete_cookie(
        key="assetguard_session",
        path="/",
        secure=True,
        httponly=True,
        samesite="strict",
    )
    return {"ok": True}


@app.get("/api/v1/auth/me")
def auth_me(identity: SessionIdentity = Depends(require_identity)):
    return {"authenticated": True, "username": identity.username, "role": identity.role}


@app.post("/api/v1/enroll", response_model=EnrollResponse)
def enroll(payload: EnrollRequest, request: Request, db: Session = Depends(db_session)):
    enrollment_code = consume_enrollment_code(payload.enrollment_token, payload.platform, db)

    device = None
    if payload.hardware_uuid:
        device = db.scalar(select(Device).where(Device.hardware_uuid == payload.hardware_uuid))
    if device is None and payload.serial:
        device = db.scalar(
            select(Device).where(
                Device.serial == payload.serial,
                Device.platform == payload.platform,
            )
        )

    event_type = "DEVICE_REENROLLED" if device is not None else "DEVICE_ENROLLED"
    if device is None:
        device = Device(
            hostname=payload.hostname,
            platform=payload.platform,
            token_hash=sha256(secrets.token_urlsafe(48)),
        )
        db.add(device)
        db.flush()

    device.hostname = payload.hostname
    device.serial = payload.serial
    device.platform = payload.platform
    device.os_version = payload.os_version
    device.architecture = payload.architecture
    device.agent_version = payload.agent_version
    device.manufacturer = payload.manufacturer
    device.model = payload.model
    device.hardware_uuid = payload.hardware_uuid
    if enrollment_code is not None and enrollment_code.branch:
        device.branch = enrollment_code.branch
    now = datetime.now(timezone.utc)
    raw_token = issue_device_auth(device, now)
    device.public_ip = client_ip(request)
    apply_network_location(device, lookup_network_location(device.public_ip), now)
    device.last_seen = now

    enrollment_detail = f"{device.platform}:{device.hostname}"
    if enrollment_code is not None:
        enrollment_detail += f";enrollment_code={enrollment_code.id}"
    db.add(AuditEvent(event_type=event_type, device_id=device.id, detail=enrollment_detail))
    db.add(DeviceObservation(
        device_id=device.id,
        reason=event_type,
        public_ip=device.public_ip,
        geo_country_code=device.geo_country_code,
        geo_region_name=device.geo_region_name,
        geo_city_name=device.geo_city_name,
        geo_accuracy_km=device.geo_accuracy_km,
    ))
    db.commit()
    return EnrollResponse(device_id=device.id, device_token=raw_token, heartbeat_seconds=HEARTBEAT_SECONDS)


@app.post("/api/v1/heartbeat")
def heartbeat(
    payload: HeartbeatRequest,
    request: Request,
    device: Device = Depends(device_from_auth),
    db: Session = Depends(db_session),
):
    previous = {
        "username": device.username,
        "lan_ip": device.lan_ip,
        "wifi_ssid": device.wifi_ssid,
        "public_ip": device.public_ip,
    }
    new_public_ip = client_ip(request)

    for field in (
        "username",
        "lan_ip",
        "hostname",
        "serial",
        "os_version",
        "architecture",
        "agent_version",
        "wifi_ssid",
        "manufacturer",
        "model",
        "hardware_uuid",
        "battery_percent",
        "bitlocker_status",
        "tpm_status",
        "antivirus_status",
    ):
        value = getattr(payload, field)
        if value is not None and value != "":
            setattr(device, field, value)

    device.public_ip = new_public_ip
    now = datetime.now(timezone.utc)
    public_ip_changed = previous["public_ip"] != device.public_ip
    if public_ip_changed or device.geo_updated_at is None:
        apply_network_location(device, lookup_network_location(device.public_ip), now)

    if device.offline_since is not None:
        offline_since = as_utc(device.offline_since)
        duration_seconds = max(0, int((now - offline_since).total_seconds()))
        db.add(AuditEvent(
            event_type="DEVICE_ONLINE_RESTORED",
            device_id=device.id,
            actor="system",
            detail=f"offline_seconds={duration_seconds}",
        ))
        device.offline_since = None

    device.last_seen = now

    network_changed = any((
        previous["lan_ip"] != device.lan_ip,
        previous["wifi_ssid"] != device.wifi_ssid,
        previous["public_ip"] != device.public_ip,
    ))
    user_changed = previous["username"] != device.username

    observation_reason = None
    if device.lost_mode:
        observation_reason = "LOST_MODE_HEARTBEAT"
    elif network_changed:
        observation_reason = "NETWORK_CHANGE"
    elif user_changed:
        observation_reason = "USER_CHANGE"

    if observation_reason:
        db.add(DeviceObservation(
            device_id=device.id,
            reason=observation_reason,
            username=device.username,
            lan_ip=device.lan_ip,
            public_ip=device.public_ip,
            wifi_ssid=device.wifi_ssid,
            geo_country_code=device.geo_country_code,
            geo_region_name=device.geo_region_name,
            geo_city_name=device.geo_city_name,
            geo_accuracy_km=device.geo_accuracy_km,
            battery_percent=device.battery_percent,
        ))

    rotated_token = None
    now = datetime.now(timezone.utc)
    if should_rotate_device_auth(device, now):
        rotated_token = issue_device_auth(device, now)
        db.add(AuditEvent(
            event_type="DEVICE_AUTH_ROTATED",
            device_id=device.id,
            actor="system",
            detail=f"generation={device.auth_generation}",
        ))

    db.commit()

    return {
        "ok": True,
        "device_id": device.id,
        "lost_mode": device.lost_mode,
        "next_heartbeat_seconds": 60 if device.lost_mode else HEARTBEAT_SECONDS,
        "device_token": rotated_token,
        "auth_expires_at": device.auth_expires_at.isoformat() if device.auth_expires_at else None,
    }


@app.post("/api/v1/software-inventory")
def sync_software_inventory(
    payload: SoftwareInventorySync,
    device: Device = Depends(device_from_auth),
    db: Session = Depends(db_session),
):
    now = datetime.now(timezone.utc)
    existing = db.scalars(
        select(InstalledApplication).where(InstalledApplication.device_id == device.id)
    ).all()
    by_key = {item.app_key: item for item in existing}
    seen: set[str] = set()
    added = 0

    for app_item in payload.applications:
        key = software_app_key(
            app_item.name,
            app_item.version,
            app_item.publisher,
            app_item.source,
        )
        if key in seen:
            continue
        seen.add(key)

        item = by_key.get(key)
        if item is None:
            item = InstalledApplication(
                device_id=device.id,
                app_key=key,
                name=app_item.name.strip(),
                version=(app_item.version or "").strip() or None,
                publisher=(app_item.publisher or "").strip() or None,
                source=(app_item.source or "").strip() or None,
                is_present=True,
                first_seen=now,
                last_seen=now,
            )
            db.add(item)
            added += 1
        else:
            item.is_present = True
            item.last_seen = now

    removed = 0
    for item in existing:
        if item.app_key not in seen and item.is_present:
            item.is_present = False
            item.last_seen = now
            removed += 1

    db.add(AuditEvent(
        event_type="SOFTWARE_INVENTORY_SYNC",
        device_id=device.id,
        actor="agent",
        detail=f"present={len(seen)};added={added};removed={removed}",
    ))
    db.commit()
    return {"ok": True, "present": len(seen), "added": added, "removed": removed}


@app.get("/api/v1/devices/{device_id}/software")
def get_software_inventory(
    device_id: str,
    include_absent: bool = False,
    _: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_SUPPORT, ROLE_AUDIT)),
    db: Session = Depends(db_session),
):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")

    query = select(InstalledApplication).where(InstalledApplication.device_id == device_id)
    if not include_absent:
        query = query.where(InstalledApplication.is_present.is_(True))

    items = db.scalars(query.order_by(InstalledApplication.name, InstalledApplication.version)).all()
    return [{
        "id": item.id,
        "name": item.name,
        "version": item.version,
        "publisher": item.publisher,
        "source": item.source,
        "is_present": item.is_present,
        "first_seen": item.first_seen.isoformat(),
        "last_seen": item.last_seen.isoformat(),
    } for item in items]


@app.post("/api/v1/software-catalog")
def create_software_catalog_item(
    payload: SoftwareCatalogCreate,
    identity: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_SUPPORT)),
    db: Session = Depends(db_session),
):
    now = datetime.now(timezone.utc)
    item = SoftwareCatalogItem(
        name=payload.name.strip(),
        publisher=(payload.publisher or "").strip() or None,
        approved_version=(payload.approved_version or "").strip() or None,
        policy=payload.policy,
        package_url=(payload.package_url or "").strip() or None,
        package_sha256=(payload.package_sha256 or "").strip().lower() or None,
        product_code=(payload.product_code or "").strip().upper() or None,
        created_by=identity.username,
        created_at=now,
        updated_at=now,
    )
    db.add(item)
    db.flush()
    db.add(AuditEvent(
        event_type="SOFTWARE_CATALOG_CREATED",
        actor=identity.username,
        detail=f"id={item.id};name={item.name};policy={item.policy}",
    ))
    db.commit()
    return {"id": item.id, "ok": True}


@app.get("/api/v1/software-catalog")
def list_software_catalog(
    _: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_SUPPORT, ROLE_AUDIT)),
    db: Session = Depends(db_session),
):
    items = db.scalars(
        select(SoftwareCatalogItem).order_by(SoftwareCatalogItem.name)
    ).all()
    return [{
        "id": item.id,
        "name": item.name,
        "publisher": item.publisher,
        "approved_version": item.approved_version,
        "policy": item.policy,
        "package_url": item.package_url,
        "package_sha256": item.package_sha256,
        "product_code": item.product_code,
        "created_by": item.created_by,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    } for item in items]


@app.patch("/api/v1/software-catalog/{catalog_id}")
def update_software_catalog_item(
    catalog_id: str,
    payload: SoftwareCatalogUpdate,
    identity: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_SUPPORT)),
    db: Session = Depends(db_session),
):
    item = db.get(SoftwareCatalogItem, catalog_id)
    if item is None:
        raise HTTPException(status_code=404, detail="software catalog item not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(item, field, value)

    item.updated_at = datetime.now(timezone.utc)
    db.add(AuditEvent(
        event_type="SOFTWARE_CATALOG_UPDATED",
        actor=identity.username,
        detail=f"id={item.id};changes={changes}",
    ))
    db.commit()
    return {"ok": True}


@app.post("/api/v1/devices/{device_id}/software-policy")
def set_device_software_policy(
    device_id: str,
    payload: DeviceSoftwareAssignmentCreate,
    identity: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_SUPPORT)),
    db: Session = Depends(db_session),
):
    if db.get(Device, device_id) is None:
        raise HTTPException(status_code=404, detail="device not found")
    if db.get(SoftwareCatalogItem, payload.catalog_id) is None:
        raise HTTPException(status_code=404, detail="software catalog item not found")

    assignment = db.scalar(
        select(DeviceSoftwareAssignment).where(
            DeviceSoftwareAssignment.device_id == device_id,
            DeviceSoftwareAssignment.catalog_id == payload.catalog_id,
        )
    )
    now = datetime.now(timezone.utc)
    if assignment is None:
        assignment = DeviceSoftwareAssignment(
            device_id=device_id,
            catalog_id=payload.catalog_id,
            desired_state=payload.desired_state,
            assigned_by=identity.username,
            assigned_at=now,
        )
        db.add(assignment)
    else:
        assignment.desired_state = payload.desired_state
        assignment.assigned_by = identity.username
        assignment.assigned_at = now

    db.add(AuditEvent(
        event_type="DEVICE_SOFTWARE_POLICY_SET",
        device_id=device_id,
        actor=identity.username,
        detail=f"catalog_id={payload.catalog_id};desired={payload.desired_state}",
    ))
    db.commit()
    return {"ok": True}


@app.get("/api/v1/devices/{device_id}/software-policy")
def get_device_software_policy(
    device_id: str,
    _: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_SUPPORT, ROLE_AUDIT)),
    db: Session = Depends(db_session),
):
    if db.get(Device, device_id) is None:
        raise HTTPException(status_code=404, detail="device not found")

    assignments = db.scalars(
        select(DeviceSoftwareAssignment).where(
            DeviceSoftwareAssignment.device_id == device_id
        )
    ).all()
    installed = db.scalars(
        select(InstalledApplication).where(
            InstalledApplication.device_id == device_id,
            InstalledApplication.is_present.is_(True),
        )
    ).all()

    output = []
    for assignment in assignments:
        catalog = db.get(SoftwareCatalogItem, assignment.catalog_id)
        if catalog is None:
            continue

        catalog_name = (catalog.name or "").strip().lower()
        catalog_publisher = (catalog.publisher or "").strip().lower()
        matches = [
            app for app in installed
            if (app.name or "").strip().lower() == catalog_name
            and (
                not catalog_publisher
                or (app.publisher or "").strip().lower() == catalog_publisher
            )
        ]

        present = bool(matches)
        installed_versions = sorted({
            (app.version or "").strip()
            for app in matches
            if (app.version or "").strip()
        })
        approved_version = (catalog.approved_version or "").strip()
        version_compliant = (
            True
            if not approved_version
            else approved_version in installed_versions
        )

        if assignment.desired_state == "REQUIRED":
            compliant = present and version_compliant
        else:
            compliant = not present

        output.append({
            "assignment_id": assignment.id,
            "catalog_id": catalog.id,
            "name": catalog.name,
            "publisher": catalog.publisher,
            "approved_version": catalog.approved_version,
            "catalog_policy": catalog.policy,
            "desired_state": assignment.desired_state,
            "present": present,
            "installed_versions": installed_versions,
            "version_compliant": version_compliant,
            "compliant": compliant,
            "assigned_by": assignment.assigned_by,
            "assigned_at": assignment.assigned_at.isoformat(),
        })

    return output


@app.post("/api/v1/devices/{device_id}/software-tasks")
def create_software_task(
    device_id: str,
    payload: SoftwareTaskCreate,
    identity: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_SUPPORT)),
    db: Session = Depends(db_session),
):
    if db.get(Device, device_id) is None:
        raise HTTPException(status_code=404, detail="device not found")
    if db.get(SoftwareCatalogItem, payload.catalog_id) is None:
        raise HTTPException(status_code=404, detail="software catalog item not found")

    task = DeviceSoftwareTask(
        device_id=device_id,
        catalog_id=payload.catalog_id,
        action=payload.action,
        status="PENDING",
        attempts=0,
        created_by=identity.username,
    )
    db.add(task)
    db.flush()
    db.add(AuditEvent(
        event_type="SOFTWARE_TASK_CREATED",
        device_id=device_id,
        actor=identity.username,
        detail=f"task_id={task.id};catalog_id={task.catalog_id};action={task.action}",
    ))
    db.commit()
    return {"id": task.id, "status": task.status}


@app.get("/api/v1/devices/{device_id}/software-tasks")
def list_device_software_tasks(
    device_id: str,
    _: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_SUPPORT, ROLE_AUDIT)),
    db: Session = Depends(db_session),
):
    if db.get(Device, device_id) is None:
        raise HTTPException(status_code=404, detail="device not found")

    tasks = db.scalars(
        select(DeviceSoftwareTask)
        .where(DeviceSoftwareTask.device_id == device_id)
        .order_by(DeviceSoftwareTask.created_at.desc())
    ).all()
    return [{
        "id": task.id,
        "catalog_id": task.catalog_id,
        "action": task.action,
        "status": task.status,
        "attempts": task.attempts,
        "created_by": task.created_by,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "result_detail": task.result_detail,
    } for task in tasks]


@app.get("/api/v1/device-tasks/pending")
def list_pending_device_tasks(
    device: Device = Depends(device_from_auth),
    db: Session = Depends(db_session),
):
    tasks = db.scalars(
        select(DeviceSoftwareTask)
        .where(
            DeviceSoftwareTask.device_id == device.id,
            DeviceSoftwareTask.status == "PENDING",
        )
        .order_by(DeviceSoftwareTask.created_at)
        .limit(20)
    ).all()

    output = []
    for task in tasks:
        catalog = db.get(SoftwareCatalogItem, task.catalog_id)
        if catalog is None:
            continue
        output.append({
            "id": task.id,
            "action": task.action,
            "catalog_id": catalog.id,
            "name": catalog.name,
            "publisher": catalog.publisher,
            "approved_version": catalog.approved_version,
        })
    return output


@app.post("/api/v1/device-tasks/{task_id}/result")
def complete_device_software_task(
    task_id: str,
    payload: SoftwareTaskResult,
    device: Device = Depends(device_from_auth),
    db: Session = Depends(db_session),
):
    task = db.get(DeviceSoftwareTask, task_id)
    if task is None or task.device_id != device.id:
        raise HTTPException(status_code=404, detail="task not found")
    if task.status in {"SUCCEEDED", "FAILED"}:
        raise HTTPException(status_code=409, detail="task already completed")

    now = datetime.now(timezone.utc)
    task.status = payload.status
    task.completed_at = now
    task.result_detail = payload.detail
    task.attempts = max(1, task.attempts)
    db.add(AuditEvent(
        event_type="SOFTWARE_TASK_COMPLETED",
        device_id=device.id,
        actor="agent",
        detail=f"task_id={task.id};status={task.status}",
    ))
    db.commit()
    return {"ok": True, "status": task.status}


@app.get("/api/v1/operations/summary")
def operations_summary(
    _: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_SUPPORT, ROLE_AUDIT)),
    db: Session = Depends(db_session),
):
    now = datetime.now(timezone.utc)
    devices = db.scalars(select(Device)).all()
    online = 0
    offline = 0
    lost = 0
    by_platform: dict[str, int] = {}

    for device in devices:
        age = max(0, int((now - as_utc(device.last_seen)).total_seconds()))
        if age <= OFFLINE_SECONDS:
            online += 1
        else:
            offline += 1
        if device.lost_mode:
            lost += 1
        platform = device.platform or "unknown"
        by_platform[platform] = by_platform.get(platform, 0) + 1

    return {
        "total": len(devices),
        "online": online,
        "offline": offline,
        "lost_mode": lost,
        "by_platform": by_platform,
        "generated_at": now.isoformat(),
    }


@app.get("/api/v1/devices")
def list_devices(_: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_SUPPORT, ROLE_AUDIT)), db: Session = Depends(db_session)):
    now = datetime.now(timezone.utc)
    devices = db.scalars(select(Device).order_by(Device.last_seen.desc())).all()
    output = []
    for d in devices:
        age = max(0, int((now - as_utc(d.last_seen)).total_seconds()))
        output.append({
            "id": d.id,
            "hostname": d.hostname,
            "serial": d.serial,
            "asset_tag": d.asset_tag,
            "branch": d.branch,
            "assigned_to": d.assigned_to,
            "username": d.username,
            "lan_ip": d.lan_ip,
            "public_ip": d.public_ip,
            "wifi_ssid": d.wifi_ssid,
            "geo_country_code": d.geo_country_code,
            "geo_country_name": d.geo_country_name,
            "geo_region_name": d.geo_region_name,
            "geo_city_name": d.geo_city_name,
            "geo_accuracy_km": d.geo_accuracy_km,
            "geo_updated_at": d.geo_updated_at.isoformat() if d.geo_updated_at else None,
            "platform": d.platform,
            "os_version": d.os_version,
            "architecture": d.architecture,
            "agent_version": d.agent_version,
            "manufacturer": d.manufacturer,
            "model": d.model,
            "hardware_uuid": d.hardware_uuid,
            "battery_percent": d.battery_percent,
            "bitlocker_status": d.bitlocker_status,
            "tpm_status": d.tpm_status,
            "antivirus_status": d.antivirus_status,
            "lost_mode": d.lost_mode,
            "auth_generation": d.auth_generation,
            "auth_expires_at": d.auth_expires_at.isoformat() if d.auth_expires_at else None,
            "auth_revoked_at": d.auth_revoked_at.isoformat() if d.auth_revoked_at else None,
            "offline_since": d.offline_since.isoformat() if d.offline_since else None,
            "last_seen": d.last_seen.isoformat(),
            "online": age <= OFFLINE_SECONDS,
        })
    return output


@app.get("/api/v1/devices/{device_id}")
def get_device(device_id: str, _: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_SUPPORT, ROLE_AUDIT)), db: Session = Depends(db_session)):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")
    return {
        "id": device.id,
        "hostname": device.hostname,
        "serial": device.serial,
        "asset_tag": device.asset_tag,
        "branch": device.branch,
        "assigned_to": device.assigned_to,
        "username": device.username,
        "lan_ip": device.lan_ip,
        "public_ip": device.public_ip,
        "wifi_ssid": device.wifi_ssid,
        "geo_country_code": device.geo_country_code,
        "geo_country_name": device.geo_country_name,
        "geo_region_name": device.geo_region_name,
        "geo_city_name": device.geo_city_name,
        "geo_accuracy_km": device.geo_accuracy_km,
        "geo_updated_at": device.geo_updated_at.isoformat() if device.geo_updated_at else None,
        "platform": device.platform,
        "os_version": device.os_version,
        "architecture": device.architecture,
        "agent_version": device.agent_version,
        "manufacturer": device.manufacturer,
        "model": device.model,
        "hardware_uuid": device.hardware_uuid,
        "battery_percent": device.battery_percent,
        "bitlocker_status": device.bitlocker_status,
        "tpm_status": device.tpm_status,
        "antivirus_status": device.antivirus_status,
        "lost_mode": device.lost_mode,
        "auth_generation": device.auth_generation,
        "auth_expires_at": device.auth_expires_at.isoformat() if device.auth_expires_at else None,
        "auth_revoked_at": device.auth_revoked_at.isoformat() if device.auth_revoked_at else None,
        "offline_since": device.offline_since.isoformat() if device.offline_since else None,
        "created_at": device.created_at.isoformat(),
        "last_seen": device.last_seen.isoformat(),
    }


@app.get("/api/v1/devices/{device_id}/history")
def device_history(
    device_id: str,
    _: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_SUPPORT, ROLE_AUDIT)),
    db: Session = Depends(db_session),
):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")

    observations = db.scalars(
        select(DeviceObservation)
        .where(DeviceObservation.device_id == device_id)
        .order_by(DeviceObservation.created_at.desc())
        .limit(500)
    ).all()

    return [{
        "id": item.id,
        "reason": item.reason,
        "username": item.username,
        "lan_ip": item.lan_ip,
        "public_ip": item.public_ip,
        "wifi_ssid": item.wifi_ssid,
        "geo_country_code": item.geo_country_code,
        "geo_region_name": item.geo_region_name,
        "geo_city_name": item.geo_city_name,
        "geo_accuracy_km": item.geo_accuracy_km,
        "battery_percent": item.battery_percent,
        "created_at": item.created_at.isoformat(),
    } for item in observations]


@app.patch("/api/v1/devices/{device_id}")
def update_device(
    device_id: str,
    payload: DeviceUpdate,
    identity: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_SUPPORT)),
    db: Session = Depends(db_session),
):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(device, field, value)
    db.add(AuditEvent(event_type="DEVICE_UPDATED", device_id=device.id, actor=identity.username, detail=str(changes)))
    db.commit()
    return {"ok": True}


@app.post("/api/v1/devices/{device_id}/lost-mode")
def set_lost_mode(
    device_id: str,
    payload: LostModeUpdate,
    identity: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_SUPPORT)),
    db: Session = Depends(db_session),
):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")
    device.lost_mode = payload.enabled
    db.add(AuditEvent(
        event_type="LOST_MODE_ENABLED" if payload.enabled else "LOST_MODE_DISABLED",
        device_id=device.id,
        actor=identity.username,
        detail=payload.reason,
    ))
    db.commit()
    return {"ok": True, "lost_mode": device.lost_mode}


@app.post("/api/v1/devices/{device_id}/revoke-auth")
def revoke_device_auth(
    device_id: str,
    payload: DeviceAuthRevoke,
    identity: SessionIdentity = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(db_session),
):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")

    now = datetime.now(timezone.utc)
    device.auth_revoked_at = now
    device.auth_expires_at = now
    device.token_hash = sha256(secrets.token_urlsafe(64))
    db.add(AuditEvent(
        event_type="DEVICE_AUTH_REVOKED",
        device_id=device.id,
        actor=identity.username,
        detail=payload.reason,
    ))
    db.commit()
    return {"ok": True, "revoked": True}


@app.get("/api/v1/audit")
def audit(_: SessionIdentity = Depends(require_roles(ROLE_ADMIN, ROLE_AUDIT)), db: Session = Depends(db_session)):
    events = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(200)).all()
    return [{
        "id": e.id,
        "event_type": e.event_type,
        "device_id": e.device_id,
        "actor": e.actor,
        "detail": e.detail,
        "created_at": e.created_at.isoformat(),
    } for e in events]
