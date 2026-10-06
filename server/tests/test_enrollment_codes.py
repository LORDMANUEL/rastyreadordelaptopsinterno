from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.enrollment_models import EnrollmentCode
from app.main import app, sha256


def add_code(raw: str, *, platform: str | None = None, branch: str | None = None, minutes: int = 30, max_uses: int = 1):
    with SessionLocal() as db:
        code = EnrollmentCode(
            code_hash=sha256(raw),
            label="CI enrollment",
            branch=branch,
            platform=platform,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=minutes),
            max_uses=max_uses,
            use_count=0,
            created_by="ci",
        )
        db.add(code)
        db.commit()
        db.refresh(code)
        return code.id


def enroll(client: TestClient, raw: str, *, platform: str = "windows"):
    return client.post(
        "/api/v1/enroll",
        json={
            "enrollment_token": raw,
            "hostname": "YUDE-ENROLL-" + uuid4().hex[:8],
            "serial": "ENR-" + uuid4().hex[:10],
            "platform": platform,
            "hardware_uuid": str(uuid4()),
        },
    )


def test_one_time_enrollment_code_sets_branch_and_exhausts():
    raw = "ci-one-time-" + uuid4().hex
    add_code(raw, platform="windows", branch="SPS", max_uses=1)

    with TestClient(app) as client:
        first = enroll(client, raw)
        assert first.status_code == 200, first.text

        detail = client.get(
            f"/api/v1/devices/{first.json()['device_id']}",
            headers={"X-Admin-Token": "ci-admin-token"},
        )
        assert detail.status_code == 200
        assert detail.json()["branch"] == "SPS"

        second = enroll(client, raw)
        assert second.status_code == 403
        assert "exhausted" in second.json()["detail"]


def test_expired_enrollment_code_is_rejected():
    raw = "ci-expired-" + uuid4().hex
    add_code(raw, platform="windows", minutes=-1)

    with TestClient(app) as client:
        response = enroll(client, raw)
        assert response.status_code == 403
        assert "expired" in response.json()["detail"]


def test_enrollment_code_platform_scope_is_enforced():
    raw = "ci-platform-" + uuid4().hex
    add_code(raw, platform="android")

    with TestClient(app) as client:
        response = enroll(client, raw, platform="windows")
        assert response.status_code == 403
        assert "platform mismatch" in response.json()["detail"]
