from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_software_inventory_tracks_present_and_removed():
    with TestClient(app) as client:
        enrolled = client.post(
            "/api/v1/enroll",
            json={
                "enrollment_token": "ci-enrollment-token",
                "hostname": "YUDE-SOFTWARE-TEST",
                "serial": "SW-" + uuid4().hex[:10],
                "platform": "windows",
                "hardware_uuid": str(uuid4()),
            },
        )
        assert enrolled.status_code == 200, enrolled.text
        data = enrolled.json()
        headers = {"Authorization": "Bearer " + data["device_token"]}

        first = client.post(
            "/api/v1/software-inventory",
            headers=headers,
            json={
                "applications": [
                    {
                        "name": "Example Browser",
                        "version": "1.0",
                        "publisher": "Example Corp",
                        "source": "registry-64",
                    },
                    {
                        "name": "Example Utility",
                        "version": "2.0",
                        "publisher": "Example Corp",
                        "source": "registry-64",
                    },
                ]
            },
        )
        assert first.status_code == 200, first.text
        assert first.json()["present"] == 2
        assert first.json()["added"] == 2

        second = client.post(
            "/api/v1/software-inventory",
            headers=headers,
            json={
                "applications": [
                    {
                        "name": "Example Browser",
                        "version": "1.0",
                        "publisher": "Example Corp",
                        "source": "registry-64",
                    }
                ]
            },
        )
        assert second.status_code == 200, second.text
        assert second.json()["present"] == 1
        assert second.json()["removed"] == 1

        present = client.get(
            f"/api/v1/devices/{data['device_id']}/software",
            headers={"X-Admin-Token": "ci-admin-token"},
        )
        assert present.status_code == 200
        assert [item["name"] for item in present.json()] == ["Example Browser"]

        all_items = client.get(
            f"/api/v1/devices/{data['device_id']}/software?include_absent=true",
            headers={"X-Admin-Token": "ci-admin-token"},
        )
        assert all_items.status_code == 200
        by_name = {item["name"]: item for item in all_items.json()}
        assert by_name["Example Browser"]["is_present"] is True
        assert by_name["Example Utility"]["is_present"] is False
