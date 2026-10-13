#!/usr/bin/env python3
import argparse
import base64
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

ADMIN_COMPONENT = "com.yude.assetguard/.YudeDeviceAdminReceiver"


def require_https(value: str, name: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise SystemExit(f"{name} must be an HTTPS URL")
    return value.rstrip("/")


def package_checksum(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def build_payload(apk_url: str, checksum: str, server_url: str, enrollment_token: str) -> dict:
    return {
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME": ADMIN_COMPONENT,
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION": apk_url,
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM": checksum,
        "android.app.extra.PROVISIONING_ADMIN_EXTRAS_BUNDLE": {
            "server_url": server_url,
            "enrollment_token": enrollment_token,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate YUDE Android Enterprise provisioning payload")
    parser.add_argument("--apk", required=True, type=Path)
    parser.add_argument("--apk-url", required=True)
    parser.add_argument("--server-url", required=True)
    parser.add_argument("--enrollment-token", required=True)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--qr-output", type=Path)
    args = parser.parse_args()

    if not args.apk.is_file():
        raise SystemExit("APK file not found")
    if not args.enrollment_token.strip():
        raise SystemExit("enrollment token is required")

    apk_url = require_https(args.apk_url, "apk-url")
    server_url = require_https(args.server_url, "server-url")
    payload = build_payload(
        apk_url=apk_url,
        checksum=package_checksum(args.apk),
        server_url=server_url,
        enrollment_token=args.enrollment_token.strip(),
    )
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

    if args.json_output:
        args.json_output.write_text(raw + "\n", encoding="utf-8")

    if args.qr_output:
        try:
            import qrcode
        except ImportError as exc:
            raise SystemExit(
                "QR output requires: python -m pip install -r ops/requirements-android-qr.txt"
            ) from exc
        image = qrcode.make(raw)
        image.save(args.qr_output)

    print(raw)


if __name__ == "__main__":
    main()
