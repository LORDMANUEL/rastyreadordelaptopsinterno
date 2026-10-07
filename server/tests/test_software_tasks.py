from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def enroll_windows(client: TestClient, hostname: str):
    return client.post(
        "/api/v1/enroll",
        json={
            "enrollment_token": "ci-enrollment-token",
            "hostname": hostname,
            "serial": "TASK-" + uuid4().hex[:10],
            "platform": "windows",
            "hardware_uuid": str(uuid4()),
        },
    )


def create_deployable_catalog(client: TestClient, headers: dict[str, str]):
    return client.post(
        "/api/v1/software-catalog",
        headers=headers,
        json={
            "name": "Approved MSI",
            "publisher": "Example Corp",
            "approved_version": "1.0",
            "policy": "ALLOWED",
            "package_url": "https://downloads.example.com/approved.msi",
            "package_sha256": "a" * 64,
            "product_code": "{12345678-1234-1234-1234-1234567890AB}",
        },
    )


def test_install_task_requires_deployment_metadata():
    with TestClient(app) as client:
        admin_headers = {"X-Admin-Token": "ci-admin-token"}
        device = enroll_windows(client, "YUDE-TASK-META")
        assert device.status_code == 200

        catalog = client.post(
            "/api/v1/software-catalog",
            headers=admin_headers,
            json={
                "name": "Inventory Only",
                "publisher": "Example Corp",
                "approved_version": "1.0",
                "policy": "ALLOWED",
            },
        )
        assert catalog.status_code == 200

        created = client.post(
            f"/api/v1/devices/{device.json()['device_id']}/software-tasks",
            headers=admin_headers,
            json={"catalog_id": catalog.json()["id"], "action": "INSTALL"},
        )
        assert created.status_code == 400


def test_software_task_queue_claim_and_completion():
    with TestClient(app) as client:
        admin_headers = {"X-Admin-Token": "ci-admin-token"}

        first = enroll_windows(client, "YUDE-TASK-01")
        second = enroll_windows(client, "YUDE-TASK-02")
        assert first.status_code == 200
        assert second.status_code == 200

        catalog = create_deployable_catalog(client, admin_headers)
        assert catalog.status_code == 200, catalog.text

        created = client.post(
            f"/api/v1/devices/{first.json()['device_id']}/software-tasks",
            headers=admin_headers,
            json={"catalog_id": catalog.json()["id"], "action": "INSTALL"},
        )
        assert created.status_code == 200, created.text
        task_id = created.json()["id"]

        first_headers = {"Authorization": "Bearer " + first.json()["device_token"]}
        second_headers = {"Authorization": "Bearer " + second.json()["device_token"]}

        first_pending = client.get("/api/v1/device-tasks/pending", headers=first_headers)
        assert first_pending.status_code == 200
        assert [item["id"] for item in first_pending.json()] == [task_id]
        assert first_pending.json()[0]["package_url"].startswith("https://")
        assert first_pending.json()[0]["package_sha256"] == "a" * 64

        second_pending = client.get("/api/v1/device-tasks/pending", headers=second_headers)
        assert second_pending.status_code == 200
        assert second_pending.json() == []

        before_claim = client.post(
            f"/api/v1/device-tasks/{task_id}/result",
            headers=first_headers,
            json={"status": "SUCCEEDED", "detail": "not claimed"},
        )
        assert before_claim.status_code == 409

        claimed = client.post(
            f"/api/v1/device-tasks/{task_id}/claim",
            headers=first_headers,
        )
        assert claimed.status_code == 200, claimed.text
        assert claimed.json()["status"] == "RUNNING"
        assert claimed.json()["attempts"] == 1
        assert claimed.json()["lease_expires_at"]

        repeated_claim = client.post(
            f"/api/v1/device-tasks/{task_id}/claim",
            headers=first_headers,
        )
        assert repeated_claim.status_code == 409

        completed = client.post(
            f"/api/v1/device-tasks/{task_id}/result",
            headers=first_headers,
            json={"status": "SUCCEEDED", "detail": "test completion"},
        )
        assert completed.status_code == 200

        repeated = client.post(
            f"/api/v1/device-tasks/{task_id}/result",
            headers=first_headers,
            json={"status": "SUCCEEDED", "detail": "duplicate"},
        )
        assert repeated.status_code == 409

        wrong_device = client.post(
            f"/api/v1/device-tasks/{task_id}/result",
            headers=second_headers,
            json={"status": "FAILED", "detail": "wrong device"},
        )
        assert wrong_device.status_code == 404

        listed = client.get(
            f"/api/v1/devices/{first.json()['device_id']}/software-tasks",
            headers=admin_headers,
        )
        assert listed.status_code == 200
        assert listed.json()[0]["status"] == "SUCCEEDED"
        assert listed.json()[0]["attempts"] == 1
        assert listed.json()[0]["lease_expires_at"] is None


def test_uninstall_task_requires_product_code():
    with TestClient(app) as client:
        admin_headers = {"X-Admin-Token": "ci-admin-token"}
        device = enroll_windows(client, "YUDE-TASK-UNINSTALL")
        assert device.status_code == 200

        catalog = client.post(
            "/api/v1/software-catalog",
            headers=admin_headers,
            json={
                "name": "No Product Code",
                "publisher": "Example Corp",
                "approved_version": "1.0",
                "policy": "ALLOWED",
                "package_url": "https://downloads.example.com/approved.msi",
                "package_sha256": "b" * 64,
            },
        )
        assert catalog.status_code == 200

        created = client.post(
            f"/api/v1/devices/{device.json()['device_id']}/software-tasks",
            headers=admin_headers,
            json={"catalog_id": catalog.json()["id"], "action": "UNINSTALL"},
        )
        assert created.status_code == 400
