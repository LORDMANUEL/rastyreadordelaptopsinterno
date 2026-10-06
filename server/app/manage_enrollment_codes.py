import argparse
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from .database import SessionLocal
from .enrollment_models import EnrollmentCode
from .main import sha256


def create_code(args) -> None:
    raw = secrets.token_urlsafe(18)
    now = datetime.now(timezone.utc)
    code = EnrollmentCode(
        code_hash=sha256(raw),
        label=args.label,
        branch=args.branch,
        platform=args.platform.lower() if args.platform else None,
        expires_at=now + timedelta(minutes=args.expires_minutes),
        max_uses=args.max_uses,
        use_count=0,
        created_by=args.created_by,
        created_at=now,
    )
    with SessionLocal() as db:
        db.add(code)
        db.commit()
        db.refresh(code)
    print("ID=" + code.id)
    print("CODE=" + raw)
    print("EXPIRES_AT=" + code.expires_at.isoformat())


def list_codes() -> None:
    with SessionLocal() as db:
        codes = db.scalars(
            select(EnrollmentCode).order_by(EnrollmentCode.created_at.desc()).limit(500)
        ).all()
        for code in codes:
            print(
                "\t".join([
                    code.id,
                    code.label or "-",
                    code.branch or "-",
                    code.platform or "-",
                    f"{code.use_count}/{code.max_uses}",
                    code.expires_at.isoformat(),
                    "REVOKED" if code.revoked_at else "ACTIVE",
                ])
            )


def revoke_code(code_id: str) -> None:
    with SessionLocal() as db:
        code = db.get(EnrollmentCode, code_id)
        if code is None:
            raise SystemExit("Código no encontrado")
        code.revoked_at = datetime.now(timezone.utc)
        db.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("--label")
    create.add_argument("--branch")
    create.add_argument("--platform", choices=["windows", "android"])
    create.add_argument("--expires-minutes", type=int, default=60)
    create.add_argument("--max-uses", type=int, default=1)
    create.add_argument("--created-by", default="server-cli")

    sub.add_parser("list")

    revoke = sub.add_parser("revoke")
    revoke.add_argument("code_id")

    args = parser.parse_args()
    if args.command == "create":
        if args.expires_minutes < 5 or args.expires_minutes > 10080:
            raise SystemExit("expires-minutes fuera de rango")
        if args.max_uses < 1 or args.max_uses > 100:
            raise SystemExit("max-uses fuera de rango")
        create_code(args)
    elif args.command == "list":
        list_codes()
    else:
        revoke_code(args.code_id)


if __name__ == "__main__":
    main()
