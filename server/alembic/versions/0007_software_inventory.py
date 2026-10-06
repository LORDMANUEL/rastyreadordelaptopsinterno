"""installed application inventory

Revision ID: 0007_software_inventory
Revises: 0006_network_geolocation
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_software_inventory"
down_revision = "0006_network_geolocation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "installed_applications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("device_id", sa.String(length=36), nullable=False),
        sa.Column("app_key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=120), nullable=True),
        sa.Column("publisher", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=True),
        sa.Column("is_present", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id", "app_key", name="uq_installed_app_device_key"),
    )
    op.create_index("ix_installed_applications_device_id", "installed_applications", ["device_id"])
    op.create_index("ix_installed_applications_name", "installed_applications", ["name"])
    op.create_index("ix_installed_applications_is_present", "installed_applications", ["is_present"])


def downgrade() -> None:
    op.drop_index("ix_installed_applications_is_present", table_name="installed_applications")
    op.drop_index("ix_installed_applications_name", table_name="installed_applications")
    op.drop_index("ix_installed_applications_device_id", table_name="installed_applications")
    op.drop_table("installed_applications")
