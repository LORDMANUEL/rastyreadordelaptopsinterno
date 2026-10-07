"""windows software execution metadata

Revision ID: 0012_windows_software_execution
Revises: 0011_software_task_queue
"""

from alembic import op
import sqlalchemy as sa

revision = "0012_windows_software_execution"
down_revision = "0011_software_task_queue"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("software_catalog", sa.Column("package_url", sa.String(length=2048), nullable=True))
    op.add_column("software_catalog", sa.Column("package_sha256", sa.String(length=64), nullable=True))
    op.add_column("software_catalog", sa.Column("product_code", sa.String(length=38), nullable=True))
    op.add_column("device_software_tasks", sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("device_software_tasks", "lease_expires_at")
    op.drop_column("software_catalog", "product_code")
    op.drop_column("software_catalog", "package_sha256")
    op.drop_column("software_catalog", "package_url")
