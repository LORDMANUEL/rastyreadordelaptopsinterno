from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


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


