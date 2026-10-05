from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from .database import engine


def main() -> None:
    cfg = Config("alembic.ini")
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "devices" in tables and "alembic_version" not in tables:
        existing_columns = {column["name"] for column in inspector.get_columns("devices")}
        if "wifi_ssid" in existing_columns:
            command.stamp(cfg, "0002_extended_inventory")
        else:
            command.stamp(cfg, "0001_initial")

    command.upgrade(cfg, "head")


if __name__ == "__main__":
    main()
