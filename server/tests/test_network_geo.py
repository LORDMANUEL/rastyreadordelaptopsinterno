from uuid import uuid4

from fastapi.testclient import TestClient

import app.main as main
from app.main import app
from app.network_geo import NetworkLocation, lookup_network_location


def test_private_and_invalid_addresses_are_not_geolocated():
    assert lookup_network_location(None) is None
    assert lookup_network_location("not-an-ip") is None
    assert lookup_network_location("127.0.0.1") is None
    assert lookup_network_location("192.168.1.25") is None


def test_network_location_is_persisted(monkeypatch):
    fake_ip = "8.8.8.8"

    monkeypatch.setattr(main, "client_ip", lambda request: fake_ip)
    monkeypatch.setattr(
        main,
        "lookup_network_location",
        lambda value: NetworkLocation(
            country_code="HN",
            country_name="Honduras",
            region_name="Cortes",
            city_name="San Pedro Sula",
            accuracy_km=50,
        ),
    )

    with TestClient(app) as client:
        enrolled = client.post(
            "/api/v1/enroll",
            json={
                "enrollment_token": "ci-enrollment-token",
                "hostname": "YUDE-GEO-TEST",
                "serial": "GEO-" + uuid4().hex[:10],
                "platform": "windows",
                "hardware_uuid": str(uuid4()),
            },
        )
        assert enrolled.status_code == 200, enrolled.text
        device_id = enrolled.json()["device_id"]

        detail = client.get(
            f"/api/v1/devices/{device_id}",
            headers={"X-Admin-Token": "ci-admin-token"},
        )
        assert detail.status_code == 200, detail.text
        data = detail.json()
        assert data["public_ip"] == fake_ip
        assert data["geo_country_code"] == "HN"
        assert data["geo_region_name"] == "Cortes"
        assert data["geo_city_name"] == "San Pedro Sula"
        assert data["geo_accuracy_km"] == 50
