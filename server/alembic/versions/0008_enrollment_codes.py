"""expiring enrollment codes

Revision ID: 0008_enrollment_codes
Revises: 0007_software_inventory
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_enrollment_codes"
down_revision = "0007_software_inventory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "enrollment_codes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=True),
        sa.Column("branch", sa.String(length=100), nullable=True),
        sa.Column("platform", sa.String(length=32), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("use_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_enrollment_codes_code_hash", "enrollment_codes", ["code_hash"], unique=True)
    op.create_index("ix_enrollment_codes_expires_at", "enrollment_codes", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_enrollment_codes_expires_at", table_name="enrollment_codes")
    op.drop_index("ix_enrollment_codes_code_hash", table_name="enrollment_codes")
    op.drop_table("enrollment_codes")
