"""extended inventory columns"""

from alembic import op
import sqlalchemy as sa

revision = "0002_extended_inventory"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("devices", sa.Column("wifi_ssid", sa.String(length=255), nullable=True))
    op.add_column("devices", sa.Column("manufacturer", sa.String(length=120), nullable=True))
    op.add_column("devices", sa.Column("model", sa.String(length=160), nullable=True))
    op.add_column("devices", sa.Column("hardware_uuid", sa.String(length=120), nullable=True))
    op.add_column("devices", sa.Column("battery_percent", sa.Integer(), nullable=True))
    op.add_column("devices", sa.Column("bitlocker_status", sa.String(length=120), nullable=True))
    op.add_column("devices", sa.Column("tpm_status", sa.String(length=120), nullable=True))
    op.add_column("devices", sa.Column("antivirus_status", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("devices", "antivirus_status")
    op.drop_column("devices", "tpm_status")
    op.drop_column("devices", "bitlocker_status")
    op.drop_column("devices", "battery_percent")
    op.drop_column("devices", "hardware_uuid")
    op.drop_column("devices", "model")
    op.drop_column("devices", "manufacturer")
    op.drop_column("devices", "wifi_ssid")
