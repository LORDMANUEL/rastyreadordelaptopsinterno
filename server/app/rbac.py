import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass

ROLE_ADMIN = "ADMINISTRADOR"
ROLE_SUPPORT = "SOPORTE"
ROLE_AUDIT = "AUDITORIA"
VALID_ROLES = {ROLE_ADMIN, ROLE_SUPPORT, ROLE_AUDIT}

SESSION_SECRET = os.getenv("SESSION_SECRET", "")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "28800"))


@dataclass(frozen=True)
class SessionIdentity:
    username: str
    role: str


def derive_auth_digest(value: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    return hashlib.scrypt(
        value.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    ).hex()


def verify_auth_value(value: str, salt_hex: str, expected_digest: str) -> bool:
    try:
        candidate = derive_auth_digest(value, salt_hex)
    except ValueError:
        return False
    return secrets.compare_digest(candidate, expected_digest)


def new_auth_material(value: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    return salt, derive_auth_digest(value, salt)


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def create_session(username: str, role: str) -> str:
    if role not in VALID_ROLES:
        raise ValueError("invalid role")
    now = int(time.time())
    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + SESSION_TTL_SECONDS,
        "nonce": secrets.token_urlsafe(12),
    }
    encoded = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        encoded.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return encoded + "." + _b64encode(signature)


def parse_session(token: str) -> SessionIdentity | None:
    if not SESSION_SECRET or "." not in token:
        return None
    encoded, signature = token.split(".", 1)
    expected = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        encoded.encode("ascii"),
        hashlib.sha256,
    ).digest()
    try:
        supplied = _b64decode(signature)
        if not hmac.compare_digest(supplied, expected):
            return None
        payload = json.loads(_b64decode(encoded))
    except (ValueError, json.JSONDecodeError):
        return None

    if int(payload.get("exp", 0)) < int(time.time()):
        return None

    username = str(payload.get("sub", ""))
    role = str(payload.get("role", ""))
    if not username or role not in VALID_ROLES:
        return None
    return SessionIdentity(username=username, role=role)
