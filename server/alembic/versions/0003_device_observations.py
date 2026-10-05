"""device connectivity observations

Revision ID: 0003_device_observations
Revises: 0002_extended_inventory
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_device_observations"
down_revision = "0002_extended_inventory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "device_observations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("device_id", sa.String(length=36), nullable=False),
        sa.Column("reason", sa.String(length=48), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("lan_ip", sa.String(length=64), nullable=True),
        sa.Column("public_ip", sa.String(length=64), nullable=True),
        sa.Column("wifi_ssid", sa.String(length=255), nullable=True),
        sa.Column("battery_percent", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_device_observations_device_id", "device_observations", ["device_id"])
    op.create_index("ix_device_observations_reason", "device_observations", ["reason"])
    op.create_index("ix_device_observations_created_at", "device_observations", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_device_observations_created_at", table_name="device_observations")
    op.drop_index("ix_device_observations_reason", table_name="device_observations")
    op.drop_index("ix_device_observations_device_id", table_name="device_observations")
    op.drop_table("device_observations")
