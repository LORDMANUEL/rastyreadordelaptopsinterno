import hashlib
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import (
    ADMIN_PASSWORD_HASH,
    ADMIN_PASSWORD_SALT,
    ADMIN_USERNAME,
    SESSION_SECRET,
    SESSION_TTL_SECONDS,
    create_session,
    parse_session,
    verify_admin_credentials,
)
from .auth_schemas import LoginRequest
from .database import SessionLocal
from .models import AuditEvent, Device
from .schemas import DeviceUpdate, EnrollRequest, EnrollResponse, HeartbeatRequest, LostModeUpdate

APP_NAME = "YUDE Asset Guard"
ENROLLMENT_TOKEN = os.getenv("ENROLLMENT_TOKEN", "")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
HEARTBEAT_SECONDS = int(os.getenv("HEARTBEAT_SECONDS", "300"))
OFFLINE_SECONDS = int(os.getenv("HEARTBEAT_OFFLINE_SECONDS", "600"))
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title=APP_NAME, version="0.2.0")


@app.on_event("startup")
def startup() -> None:
    required = {
        "ENROLLMENT_TOKEN": ENROLLMENT_TOKEN,
        "ADMIN_TOKEN": ADMIN_TOKEN,
        "ADMIN_USERNAME": ADMIN_USERNAME,
        "ADMIN_PASSWORD_SALT": ADMIN_PASSWORD_SALT,
        "ADMIN_PASSWORD_HASH": ADMIN_PASSWORD_HASH,
        "SESSION_SECRET": SESSION_SECRET,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError("missing required configuration: " + ", ".join(missing))


def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require_admin(
    request: Request,
    x_admin_token: str = Header(default=""),
    assetguard_session: str | None = Cookie(default=None),
) -> str:
    if x_admin_token and secrets.compare_digest(x_admin_token, ADMIN_TOKEN):
        return "automation"

    if assetguard_session:
        identity = parse_session(assetguard_session)
        if identity is not None:
            return identity.username

    raise HTTPException(status_code=401, detail="authentication required")


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
    return device


def client_ip(request: Request) -> str | None:
    # Uvicorn's trusted proxy middleware normalizes request.client.
    # Do not trust a raw X-Forwarded-For header from arbitrary clients here.
    return request.client.host if request.client else None


@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME, "version": app.version}


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/api/v1/auth/login")
def login(payload: LoginRequest, response: Response):
    if not verify_admin_credentials(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="invalid credentials")

    response.set_cookie(
        key="assetguard_session",
        value=create_session(payload.username),
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
        max_age=SESSION_TTL_SECONDS,
    )
    return {"ok": True, "username": payload.username}


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
def auth_me(actor: str = Depends(require_admin)):
    return {"authenticated": True, "username": actor}


@app.post("/api/v1/enroll", response_model=EnrollResponse)
def enroll(payload: EnrollRequest, request: Request, db: Session = Depends(db_session)):
    if not secrets.compare_digest(payload.enrollment_token, ENROLLMENT_TOKEN):
        raise HTTPException(status_code=403, detail="invalid enrollment token")

    raw_token = secrets.token_urlsafe(48)

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
            token_hash=sha256(raw_token),
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
    device.token_hash = sha256(raw_token)
    device.public_ip = client_ip(request)
    device.last_seen = datetime.now(timezone.utc)

    db.add(AuditEvent(event_type=event_type, device_id=device.id, detail=f"{device.platform}:{device.hostname}"))
    db.commit()
    return EnrollResponse(device_id=device.id, device_token=raw_token, heartbeat_seconds=HEARTBEAT_SECONDS)


@app.post("/api/v1/heartbeat")
def heartbeat(
    payload: HeartbeatRequest,
    request: Request,
    device: Device = Depends(device_from_auth),
    db: Session = Depends(db_session),
):
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

    device.public_ip = client_ip(request)
    device.last_seen = datetime.now(timezone.utc)
    db.commit()

    return {
        "ok": True,
        "device_id": device.id,
        "lost_mode": device.lost_mode,
        "next_heartbeat_seconds": 60 if device.lost_mode else HEARTBEAT_SECONDS,
    }


@app.get("/api/v1/devices")
def list_devices(_: str = Depends(require_admin), db: Session = Depends(db_session)):
    now = datetime.now(timezone.utc)
    devices = db.scalars(select(Device).order_by(Device.last_seen.desc())).all()
    output = []
    for d in devices:
        age = max(0, int((now - d.last_seen).total_seconds()))
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
            "last_seen": d.last_seen.isoformat(),
            "online": age <= OFFLINE_SECONDS,
        })
    return output


@app.get("/api/v1/devices/{device_id}")
def get_device(device_id: str, _: str = Depends(require_admin), db: Session = Depends(db_session)):
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
        "created_at": device.created_at.isoformat(),
        "last_seen": device.last_seen.isoformat(),
    }


@app.patch("/api/v1/devices/{device_id}")
def update_device(
    device_id: str,
    payload: DeviceUpdate,
    actor: str = Depends(require_admin),
    db: Session = Depends(db_session),
):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(device, field, value)
    db.add(AuditEvent(event_type="DEVICE_UPDATED", device_id=device.id, actor=actor, detail=str(changes)))
    db.commit()
    return {"ok": True}


@app.post("/api/v1/devices/{device_id}/lost-mode")
def set_lost_mode(
    device_id: str,
    payload: LostModeUpdate,
    actor: str = Depends(require_admin),
    db: Session = Depends(db_session),
):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")
    device.lost_mode = payload.enabled
    db.add(AuditEvent(
        event_type="LOST_MODE_ENABLED" if payload.enabled else "LOST_MODE_DISABLED",
        device_id=device.id,
        actor=actor,
        detail=payload.reason,
    ))
    db.commit()
    return {"ok": True, "lost_mode": device.lost_mode}


@app.get("/api/v1/audit")
def audit(_: str = Depends(require_admin), db: Session = Depends(db_session)):
    events = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(200)).all()
    return [{
        "id": e.id,
        "event_type": e.event_type,
        "device_id": e.device_id,
        "actor": e.actor,
        "detail": e.detail,
        "created_at": e.created_at.isoformat(),
    } for e in events]
