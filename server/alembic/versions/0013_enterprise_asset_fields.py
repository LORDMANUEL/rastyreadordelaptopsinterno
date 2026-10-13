"""enterprise asset fields

Revision ID: 0013_enterprise_asset_fields
Revises: 0012_windows_software_execution
"""

from alembic import op
import sqlalchemy as sa

revision = "0013_enterprise_asset_fields"
down_revision = "0012_windows_software_execution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("devices", sa.Column("department", sa.String(length=120), nullable=True))
    op.add_column("devices", sa.Column("asset_status", sa.String(length=32), nullable=True))
    op.add_column("devices", sa.Column("physical_condition", sa.String(length=32), nullable=True))
    op.add_column("devices", sa.Column("ownership_type", sa.String(length=32), nullable=True))
    op.add_column("devices", sa.Column("lease_contract", sa.String(length=160), nullable=True))
    op.add_column("devices", sa.Column("provider", sa.String(length=180), nullable=True))
    op.add_column("devices", sa.Column("acquisition_date", sa.Date(), nullable=True))
    op.add_column("devices", sa.Column("assignment_date", sa.Date(), nullable=True))
    op.add_column("devices", sa.Column("acquisition_cost", sa.Numeric(precision=14, scale=2), nullable=True))
    op.add_column("devices", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("devices", sa.Column("last_audit_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("devices", "last_audit_at")
    op.drop_column("devices", "notes")
    op.drop_column("devices", "acquisition_cost")
    op.drop_column("devices", "assignment_date")
    op.drop_column("devices", "acquisition_date")
    op.drop_column("devices", "provider")
    op.drop_column("devices", "lease_contract")
    op.drop_column("devices", "ownership_type")
    op.drop_column("devices", "physical_condition")
    op.drop_column("devices", "asset_status")
    op.drop_column("devices", "department")
