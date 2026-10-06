from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_software_task_queue_is_device_scoped_and_audited():
    with TestClient(app) as client:
        admin_headers = {"X-Admin-Token": "ci-admin-token"}

        first = client.post(
            "/api/v1/enroll",
            json={
                "enrollment_token": "ci-enrollment-token",
                "hostname": "YUDE-TASK-01",
                "serial": "TASK-" + uuid4().hex[:10],
                "platform": "windows",
                "hardware_uuid": str(uuid4()),
            },
        )
        second = client.post(
            "/api/v1/enroll",
            json={
                "enrollment_token": "ci-enrollment-token",
                "hostname": "YUDE-TASK-02",
                "serial": "TASK-" + uuid4().hex[:10],
                "platform": "windows",
                "hardware_uuid": str(uuid4()),
            },
        )
        assert first.status_code == 200
        assert second.status_code == 200

        catalog = client.post(
            "/api/v1/software-catalog",
            headers=admin_headers,
            json={
                "name": "Approved MSI",
                "publisher": "Example Corp",
                "approved_version": "1.0",
                "policy": "ALLOWED",
            },
        )
        assert catalog.status_code == 200, catalog.text

        created = client.post(
            f"/api/v1/devices/{first.json()['device_id']}/software-tasks",
            headers=admin_headers,
            json={"catalog_id": catalog.json()["id"], "action": "INSTALL"},
        )
        assert created.status_code == 200, created.text
        task_id = created.json()["id"]

        first_pending = client.get(
            "/api/v1/device-tasks/pending",
            headers={"Authorization": "Bearer " + first.json()["device_token"]},
        )
        assert first_pending.status_code == 200
        assert [item["id"] for item in first_pending.json()] == [task_id]

        second_pending = client.get(
            "/api/v1/device-tasks/pending",
            headers={"Authorization": "Bearer " + second.json()["device_token"]},
        )
        assert second_pending.status_code == 200
        assert second_pending.json() == []

        completed = client.post(
            f"/api/v1/device-tasks/{task_id}/result",
            headers={"Authorization": "Bearer " + first.json()["device_token"]},
            json={"status": "SUCCEEDED", "detail": "test completion"},
        )
        assert completed.status_code == 200

        repeated = client.post(
            f"/api/v1/device-tasks/{task_id}/result",
            headers={"Authorization": "Bearer " + first.json()["device_token"]},
            json={"status": "SUCCEEDED", "detail": "duplicate"},
        )
        assert repeated.status_code == 409

        wrong_device = client.post(
            f"/api/v1/device-tasks/{task_id}/result",
            headers={"Authorization": "Bearer " + second.json()["device_token"]},
            json={"status": "FAILED", "detail": "wrong device"},
        )
        assert wrong_device.status_code == 404

        listed = client.get(
            f"/api/v1/devices/{first.json()['device_id']}/software-tasks",
            headers=admin_headers,
        )
        assert listed.status_code == 200
        assert listed.json()[0]["status"] == "SUCCEEDED"
