import argparse
import getpass
from datetime import datetime, timezone

from sqlalchemy import select

from .database import SessionLocal
from .rbac import VALID_ROLES, new_auth_material
from .user_models import UserAccount


def upsert_account(username: str, role: str) -> None:
    if role not in VALID_ROLES:
        raise SystemExit("Rol inválido")

    value = getpass.getpass("Clave de acceso: ")
    confirm = getpass.getpass("Confirmar clave: ")
    if value != confirm:
        raise SystemExit("Los valores no coinciden")
    if len(value) < 12:
        raise SystemExit("Use al menos 12 caracteres")

    salt, digest = new_auth_material(value)
    with SessionLocal() as db:
        account = db.scalar(select(UserAccount).where(UserAccount.username == username))
        if account is None:
            account = UserAccount(
                username=username,
                auth_salt=salt,
                auth_digest=digest,
                role=role,
                is_active=True,
            )
            db.add(account)
        else:
            account.auth_salt = salt
            account.auth_digest = digest
            account.role = role
            account.is_active = True
            account.updated_at = datetime.now(timezone.utc)
        db.commit()


def set_enabled(username: str, enabled: bool) -> None:
    with SessionLocal() as db:
        account = db.scalar(select(UserAccount).where(UserAccount.username == username))
        if account is None:
            raise SystemExit("Usuario no encontrado")
        account.is_active = enabled
        account.updated_at = datetime.now(timezone.utc)
        db.commit()


def list_accounts() -> None:
    with SessionLocal() as db:
        accounts = db.scalars(select(UserAccount).order_by(UserAccount.username)).all()
        for account in accounts:
            print(f"{account.username}\t{account.role}\t{'ACTIVO' if account.is_active else 'INACTIVO'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("set")
    create.add_argument("username")
    create.add_argument("role", choices=sorted(VALID_ROLES))

    disable = sub.add_parser("disable")
    disable.add_argument("username")

    enable = sub.add_parser("enable")
    enable.add_argument("username")

    sub.add_parser("list")

    args = parser.parse_args()
    if args.command == "set":
        upsert_account(args.username, args.role)
    elif args.command == "disable":
        set_enabled(args.username, False)
    elif args.command == "enable":
        set_enabled(args.username, True)
    else:
        list_accounts()


if __name__ == "__main__":
    main()
