from fastapi.testclient import TestClient

import app.http_security as http_security
from app.main import app


def test_security_headers_request_id_and_readiness():
    with TestClient(app) as client:
        health = client.get("/health", headers={"X-Request-ID": "request-12345"})
        assert health.status_code == 200
        assert health.headers["x-request-id"] == "request-12345"
        assert health.headers["x-content-type-options"] == "nosniff"
        assert health.headers["x-frame-options"] == "DENY"
        assert "camera=()" in health.headers["permissions-policy"]

        ready = client.get("/ready")
        assert ready.status_code == 200
        assert ready.json()["database"] == "ok"


def test_request_size_limit(monkeypatch):
    monkeypatch.setattr(http_security, "MAX_REQUEST_BYTES", 32)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            content=b"x" * 64,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 413


def test_login_rate_limit(monkeypatch):
    monkeypatch.setattr(http_security, "limiter", http_security.SlidingWindowLimiter())
    monkeypatch.setattr(http_security, "LOGIN_RATE_LIMIT", 1)
    monkeypatch.setattr(http_security, "LOGIN_RATE_WINDOW_SECONDS", 60)

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/auth/login",
            json={"username": "unknown-user", "password": "invalid-value"},
        )
        assert first.status_code in {401, 503}

        second = client.post(
            "/api/v1/auth/login",
            json={"username": "unknown-user", "password": "invalid-value"},
        )
        assert second.status_code == 429
        assert second.headers["retry-after"] == "60"


def test_cookie_authenticated_writes_require_verification_header():
    cookie = {"Cookie": "assetguard_session=invalid-session"}

    with TestClient(app, base_url="https://testserver") as client:
        blocked = client.post(
            "/api/v1/auth/logout",
            headers=cookie,
        )
        assert blocked.status_code == 403

        verified = client.post(
            "/api/v1/auth/logout",
            headers={**cookie, "X-Requested-With": "YudeAssetGuard"},
        )
        assert verified.status_code == 200
