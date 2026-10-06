from __future__ import annotations

import os
import re
import threading
import time
from collections import defaultdict, deque
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse


MAX_REQUEST_BYTES = int(os.getenv("MAX_REQUEST_BYTES", str(2 * 1024 * 1024)))
LOGIN_RATE_LIMIT = int(os.getenv("LOGIN_RATE_LIMIT", "10"))
LOGIN_RATE_WINDOW_SECONDS = int(os.getenv("LOGIN_RATE_WINDOW_SECONDS", "60"))
ENROLL_RATE_LIMIT = int(os.getenv("ENROLL_RATE_LIMIT", "30"))
ENROLL_RATE_WINDOW_SECONDS = int(os.getenv("ENROLL_RATE_WINDOW_SECONDS", "300"))

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{8,128}$")
_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            bucket = self._buckets[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True


limiter = SlidingWindowLimiter()


def request_id_for(request: Request) -> str:
    candidate = request.headers.get("x-request-id", "").strip()
    if _REQUEST_ID_RE.fullmatch(candidate):
        return candidate
    return str(uuid4())


def peer_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def security_headers(response, request_id: str) -> None:
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "connect-src 'self'; "
        "img-src 'self' data:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )


async def guard_request(request: Request, call_next):
    req_id = request_id_for(request)
    request.state.request_id = req_id

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_BYTES:
                response = JSONResponse(status_code=413, content={"detail": "request too large"})
                security_headers(response, req_id)
                return response
        except ValueError:
            response = JSONResponse(status_code=400, content={"detail": "invalid content-length"})
            security_headers(response, req_id)
            return response

    peer = peer_key(request)
    if request.method == "POST" and request.url.path == "/api/v1/auth/login":
        if not limiter.allowed("login:" + peer, LOGIN_RATE_LIMIT, LOGIN_RATE_WINDOW_SECONDS):
            response = JSONResponse(status_code=429, content={"detail": "too many login attempts"})
            response.headers["Retry-After"] = str(LOGIN_RATE_WINDOW_SECONDS)
            security_headers(response, req_id)
            return response

    if request.method == "POST" and request.url.path == "/api/v1/enroll":
        if not limiter.allowed("enroll:" + peer, ENROLL_RATE_LIMIT, ENROLL_RATE_WINDOW_SECONDS):
            response = JSONResponse(status_code=429, content={"detail": "too many enrollment attempts"})
            response.headers["Retry-After"] = str(ENROLL_RATE_WINDOW_SECONDS)
            security_headers(response, req_id)
            return response

    if (
        request.method in _WRITE_METHODS
        and request.url.path.startswith("/api/")
        and request.url.path not in {"/api/v1/auth/login"}
        and "assetguard_session" in request.cookies
        and not request.headers.get("x-admin-token")
        and request.headers.get("x-requested-with") != "YudeAssetGuard"
    ):
        response = JSONResponse(status_code=403, content={"detail": "missing request verification header"})
        security_headers(response, req_id)
        return response

    response = await call_next(request)
    security_headers(response, req_id)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response
