from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_required_software_policy_becomes_compliant_after_inventory_sync():
    with TestClient(app) as client:
        enrolled = client.post(
            "/api/v1/enroll",
            json={
                "enrollment_token": "ci-enrollment-token",
                "hostname": "YUDE-POLICY-TEST",
                "serial": "POL-" + uuid4().hex[:10],
                "platform": "windows",
                "hardware_uuid": str(uuid4()),
            },
        )
        assert enrolled.status_code == 200, enrolled.text
        device_id = enrolled.json()["device_id"]
        agent_headers = {"Authorization": "Bearer " + enrolled.json()["device_token"]}
        admin_headers = {"X-Admin-Token": "ci-admin-token"}

        catalog = client.post(
            "/api/v1/software-catalog",
            headers=admin_headers,
            json={
                "name": "Approved Browser",
                "publisher": "Example Corp",
                "approved_version": "1.0",
                "policy": "REQUIRED",
            },
        )
        assert catalog.status_code == 200, catalog.text
        catalog_id = catalog.json()["id"]

        assigned = client.post(
            f"/api/v1/devices/{device_id}/software-policy",
            headers=admin_headers,
            json={"catalog_id": catalog_id, "desired_state": "REQUIRED"},
        )
        assert assigned.status_code == 200, assigned.text

        before = client.get(
            f"/api/v1/devices/{device_id}/software-policy",
            headers=admin_headers,
        )
        assert before.status_code == 200
        assert before.json()[0]["present"] is False
        assert before.json()[0]["compliant"] is False

        synced = client.post(
            "/api/v1/software-inventory",
            headers=agent_headers,
            json={
                "applications": [
                    {
                        "name": "Approved Browser",
                        "version": "1.0",
                        "publisher": "Example Corp",
                        "source": "registry-64",
                    }
                ]
            },
        )
        assert synced.status_code == 200, synced.text

        after = client.get(
            f"/api/v1/devices/{device_id}/software-policy",
            headers=admin_headers,
        )
        assert after.status_code == 200
        assert after.json()[0]["present"] is True
        assert after.json()[0]["compliant"] is True
