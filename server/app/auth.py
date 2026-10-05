import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass


ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD_SALT = os.getenv("ADMIN_PASSWORD_SALT", "")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
SESSION_SECRET = os.getenv("SESSION_SECRET", "")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "28800"))


@dataclass(frozen=True)
class SessionIdentity:
    username: str


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def derive_password_hash(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    )
    return derived.hex()


def verify_admin_credentials(username: str, password: str) -> bool:
    if not all((ADMIN_USERNAME, ADMIN_PASSWORD_SALT, ADMIN_PASSWORD_HASH)):
        return False
    if not secrets.compare_digest(username, ADMIN_USERNAME):
        return False
    candidate = derive_password_hash(password, ADMIN_PASSWORD_SALT)
    return secrets.compare_digest(candidate, ADMIN_PASSWORD_HASH)


def create_session(username: str) -> str:
    now = int(time.time())
    payload = {
        "sub": username,
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
    if not username:
        return None
    return SessionIdentity(username=username)
