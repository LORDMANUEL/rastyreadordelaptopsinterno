"""offline observability state

Revision ID: 0010_offline_observability
Revises: 0009_software_policy_catalog
"""

from alembic import op
import sqlalchemy as sa

revision = "0010_offline_observability"
down_revision = "0009_software_policy_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "devices",
        sa.Column("offline_since", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("devices", "offline_since")
