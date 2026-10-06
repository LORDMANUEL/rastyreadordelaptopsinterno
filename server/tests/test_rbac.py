from uuid import uuid4

from fastapi.testclient import TestClient

import app.rbac as rbac
from app.database import SessionLocal
from app.main import app
from app.user_models import UserAccount


def add_account(username: str, role: str, active: bool = True) -> None:
    with SessionLocal() as db:
        db.add(UserAccount(
            username=username,
            auth_salt="test-salt",
            auth_digest="test-digest",
            role=role,
            is_active=active,
        ))
        db.commit()


def session_headers(username: str, role: str) -> dict[str, str]:
    token = rbac.create_session(username, role)
    return {"Cookie": "assetguard_session=" + token}


def test_role_permissions(monkeypatch):
    monkeypatch.setattr(rbac, "SESSION_SECRET", "ci-session-key")

    suffix = uuid4().hex[:8]
    roles = (
        ("ADMINISTRADOR", "admin-" + suffix),
        ("SOPORTE", "support-" + suffix),
        ("AUDITORIA", "audit-" + suffix),
    )
    for role, username in roles:
        add_account(username, role)

    with TestClient(app, base_url="https://testserver") as client:
        for role, username in roles:
            headers = session_headers(username, role)

            assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
            assert client.get("/api/v1/devices", headers=headers).status_code == 200

            audit = client.get("/api/v1/audit", headers=headers)
            assert audit.status_code == (403 if role == "SOPORTE" else 200)

            lost = client.post(
                "/api/v1/devices/not-a-device/lost-mode",
                headers=headers,
                json={"enabled": True, "reason": "role check"},
            )
            assert lost.status_code == (403 if role == "AUDITORIA" else 404)


def test_disabled_account_invalidates_existing_session(monkeypatch):
    monkeypatch.setattr(rbac, "SESSION_SECRET", "ci-session-key")

    username = "disabled-" + uuid4().hex[:8]
    add_account(username, "SOPORTE", active=False)

    with TestClient(app, base_url="https://testserver") as client:
        response = client.get(
            "/api/v1/devices",
            headers=session_headers(username, "SOPORTE"),
        )
        assert response.status_code == 401
