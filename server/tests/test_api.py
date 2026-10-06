from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import OFFLINE_SECONDS, app, scan_offline_devices
from app.models import Device


def test_enrollment_reenrollment_heartbeat_and_lost_mode():
    serial = "TEST-" + uuid4().hex[:10]
    hardware_uuid = str(uuid4())

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/enroll",
            json={
                "enrollment_token": "ci-enrollment-token",
                "hostname": "YUDE-TEST-01",
                "serial": serial,
                "platform": "windows",
                "os_version": "Windows Test",
                "architecture": "amd64",
                "agent_version": "0.2.0",
                "manufacturer": "Test",
                "model": "Laptop",
                "hardware_uuid": hardware_uuid,
            },
        )
        assert first.status_code == 200, first.text
        first_data = first.json()

        heartbeat = client.post(
            "/api/v1/heartbeat",
            headers={"Authorization": "Bearer " + first_data["device_token"]},
            json={"username": "YUDE\\tester", "battery_percent": 90},
        )
        assert heartbeat.status_code == 200, heartbeat.text
        assert heartbeat.json()["lost_mode"] is False

        second = client.post(
            "/api/v1/enroll",
            json={
                "enrollment_token": "ci-enrollment-token",
                "hostname": "YUDE-TEST-01",
                "serial": serial,
                "platform": "windows",
                "os_version": "Windows Test",
                "architecture": "amd64",
                "agent_version": "0.2.0",
                "manufacturer": "Test",
                "model": "Laptop",
                "hardware_uuid": hardware_uuid,
            },
        )
        assert second.status_code == 200, second.text
        second_data = second.json()

        assert second_data["device_id"] == first_data["device_id"]
        assert second_data["device_token"] != first_data["device_token"]

        old_token = client.post(
            "/api/v1/heartbeat",
            headers={"Authorization": "Bearer " + first_data["device_token"]},
            json={"username": "stale-token"},
        )
        assert old_token.status_code == 401

        new_token = client.post(
            "/api/v1/heartbeat",
            headers={"Authorization": "Bearer " + second_data["device_token"]},
            json={"username": "YUDE\\tester"},
        )
        assert new_token.status_code == 200

        lost = client.post(
            f"/api/v1/devices/{second_data['device_id']}/lost-mode",
            headers={"X-Admin-Token": "ci-admin-token"},
            json={"enabled": True, "reason": "CI theft recovery test"},
        )
        assert lost.status_code == 200, lost.text
        assert lost.json()["lost_mode"] is True

        heartbeat_lost = client.post(
            "/api/v1/heartbeat",
            headers={"Authorization": "Bearer " + second_data["device_token"]},
            json={"username": "YUDE\\tester"},
        )
        assert heartbeat_lost.status_code == 200
        assert heartbeat_lost.json()["lost_mode"] is True
        assert heartbeat_lost.json()["next_heartbeat_seconds"] == 60

        history = client.get(
            f"/api/v1/devices/{second_data['device_id']}/history",
            headers={"X-Admin-Token": "ci-admin-token"},
        )
        assert history.status_code == 200, history.text
        reasons = [item["reason"] for item in history.json()]
        assert "LOST_MODE_HEARTBEAT" in reasons
        assert any(reason in reasons for reason in ("DEVICE_ENROLLED", "DEVICE_REENROLLED"))


def test_admin_token_required():
    with TestClient(app) as client:
        response = client.get("/api/v1/devices")
        assert response.status_code == 401




def test_device_auth_rotation_and_revocation():
    serial = "ROTATE-" + uuid4().hex[:10]
    hardware_uuid = str(uuid4())

    with TestClient(app) as client:
        enrolled = client.post(
            "/api/v1/enroll",
            json={
                "enrollment_token": "ci-enrollment-token",
                "hostname": "YUDE-ROTATE-01",
                "serial": serial,
                "platform": "windows",
                "hardware_uuid": hardware_uuid,
            },
        )
        assert enrolled.status_code == 200, enrolled.text
        data = enrolled.json()
        original = data["device_token"]

        with SessionLocal() as db:
            device = db.get(Device, data["device_id"])
            device.auth_issued_at = datetime.now(timezone.utc) - timedelta(days=8)
            db.commit()

        rotated = client.post(
            "/api/v1/heartbeat",
            headers={"Authorization": "Bearer " + original},
            json={"username": "YUDE\\rotation-test"},
        )
        assert rotated.status_code == 200, rotated.text
        replacement = rotated.json()["device_token"]
        assert replacement
        assert replacement != original

        stale = client.post(
            "/api/v1/heartbeat",
            headers={"Authorization": "Bearer " + original},
            json={"username": "stale"},
        )
        assert stale.status_code == 401

        current = client.post(
            "/api/v1/heartbeat",
            headers={"Authorization": "Bearer " + replacement},
            json={"username": "YUDE\\rotation-test"},
        )
        assert current.status_code == 200

        revoke = client.post(
            f"/api/v1/devices/{data['device_id']}/revoke-auth",
            headers={"X-Admin-Token": "ci-admin-token"},
            json={"reason": "credential lifecycle test"},
        )
        assert revoke.status_code == 200, revoke.text

        revoked = client.post(
            "/api/v1/heartbeat",
            headers={"Authorization": "Bearer " + replacement},
            json={"username": "revoked"},
        )
        assert revoked.status_code == 401


def test_offline_detection_and_recovery():
    serial = "OFFLINE-" + uuid4().hex[:10]
    hardware_uuid = str(uuid4())

    with TestClient(app) as client:
        enrolled = client.post(
            "/api/v1/enroll",
            json={
                "enrollment_token": "ci-enrollment-token",
                "hostname": "YUDE-OFFLINE-01",
                "serial": serial,
                "platform": "windows",
                "hardware_uuid": hardware_uuid,
            },
        )
        assert enrolled.status_code == 200, enrolled.text
        data = enrolled.json()

        reference = datetime.now(timezone.utc)
        with SessionLocal() as db:
            device = db.get(Device, data["device_id"])
            device.last_seen = reference - timedelta(seconds=OFFLINE_SECONDS + 30)
            device.offline_since = None
            db.commit()

            marked = scan_offline_devices(db, now=reference)
            assert marked == 1

            db.refresh(device)
            assert device.offline_since is not None

            marked_again = scan_offline_devices(db, now=reference + timedelta(seconds=5))
            assert marked_again == 0

        summary = client.get(
            "/api/v1/operations/summary",
            headers={"X-Admin-Token": "ci-admin-token"},
        )
        assert summary.status_code == 200, summary.text
        assert summary.json()["offline"] >= 1

        heartbeat = client.post(
            "/api/v1/heartbeat",
            headers={"Authorization": "Bearer " + data["device_token"]},
            json={"username": "YUDE\\offline-test"},
        )
        assert heartbeat.status_code == 200, heartbeat.text

        with SessionLocal() as db:
            device = db.get(Device, data["device_id"])
            assert device.offline_since is None

        audit = client.get(
            "/api/v1/audit",
            headers={"X-Admin-Token": "ci-admin-token"},
        )
        assert audit.status_code == 200
        events = [
            item["event_type"]
            for item in audit.json()
            if item["device_id"] == data["device_id"]
        ]
        assert "DEVICE_OFFLINE" in events
        assert "DEVICE_ONLINE_RESTORED" in events
