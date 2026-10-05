"""initial schema"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("serial", sa.String(length=255), nullable=True),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("os_version", sa.String(length=255), nullable=True),
        sa.Column("architecture", sa.String(length=64), nullable=True),
        sa.Column("agent_version", sa.String(length=64), nullable=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("asset_tag", sa.String(length=100), nullable=True),
        sa.Column("branch", sa.String(length=100), nullable=True),
        sa.Column("assigned_to", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("lan_ip", sa.String(length=64), nullable=True),
        sa.Column("public_ip", sa.String(length=64), nullable=True),
        sa.Column("lost_mode", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_devices_hostname", "devices", ["hostname"])
    op.create_index("ix_devices_serial", "devices", ["serial"])
    op.create_index("ix_devices_token_hash", "devices", ["token_hash"], unique=True)
    op.create_index("ix_devices_asset_tag", "devices", ["asset_tag"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("device_id", sa.String(length=36), nullable=True),
        sa.Column("actor", sa.String(length=120), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_device_id", "audit_events", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_device_id", table_name="audit_events")
    op.drop_index("ix_audit_events_event_type", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_devices_asset_tag", table_name="devices")
    op.drop_index("ix_devices_token_hash", table_name="devices")
    op.drop_index("ix_devices_serial", table_name="devices")
    op.drop_index("ix_devices_hostname", table_name="devices")
    op.drop_table("devices")
