"""software policy catalog

Revision ID: 0009_software_policy_catalog
Revises: 0008_enrollment_codes
"""

from alembic import op
import sqlalchemy as sa

revision = "0009_software_policy_catalog"
down_revision = "0008_enrollment_codes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "software_catalog",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("publisher", sa.String(length=255), nullable=True),
        sa.Column("approved_version", sa.String(length=120), nullable=True),
        sa.Column("policy", sa.String(length=24), nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_software_catalog_name", "software_catalog", ["name"])
    op.create_index("ix_software_catalog_policy", "software_catalog", ["policy"])

    op.create_table(
        "device_software_assignments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("device_id", sa.String(length=36), nullable=False),
        sa.Column("catalog_id", sa.String(length=36), nullable=False),
        sa.Column("desired_state", sa.String(length=24), nullable=False),
        sa.Column("assigned_by", sa.String(length=120), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id", "catalog_id", name="uq_device_software_assignment"),
    )
    op.create_index("ix_device_software_assignments_device_id", "device_software_assignments", ["device_id"])
    op.create_index("ix_device_software_assignments_catalog_id", "device_software_assignments", ["catalog_id"])
    op.create_index("ix_device_software_assignments_desired_state", "device_software_assignments", ["desired_state"])


def downgrade() -> None:
    op.drop_index("ix_device_software_assignments_desired_state", table_name="device_software_assignments")
    op.drop_index("ix_device_software_assignments_catalog_id", table_name="device_software_assignments")
    op.drop_index("ix_device_software_assignments_device_id", table_name="device_software_assignments")
    op.drop_table("device_software_assignments")
    op.drop_index("ix_software_catalog_policy", table_name="software_catalog")
    op.drop_index("ix_software_catalog_name", table_name="software_catalog")
    op.drop_table("software_catalog")
