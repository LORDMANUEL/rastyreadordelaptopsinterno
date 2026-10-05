import getpass
import secrets

from .auth import derive_password_hash


def main() -> None:
    password = getpass.getpass("Nueva contraseña de administrador: ")
    confirm = getpass.getpass("Confirmar contraseña: ")
    if password != confirm:
        raise SystemExit("Las contraseñas no coinciden")
    if len(password) < 12:
        raise SystemExit("Use al menos 12 caracteres")

    salt = secrets.token_hex(16)
    digest = derive_password_hash(password, salt)
    print()
    print("ADMIN_PASSWORD_SALT=" + salt)
    print("ADMIN_PASSWORD_HASH=" + digest)
    print("SESSION_SECRET=" + secrets.token_urlsafe(48))


if __name__ == "__main__":
    main()
