"""device auth lifecycle

Revision ID: 0005_device_auth_lifecycle
Revises: 0004_user_accounts
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_device_auth_lifecycle"
down_revision = "0004_user_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("devices", sa.Column("auth_issued_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("devices", sa.Column("auth_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("devices", sa.Column("auth_revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("devices", sa.Column("auth_generation", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("devices", "auth_generation")
    op.drop_column("devices", "auth_revoked_at")
    op.drop_column("devices", "auth_expires_at")
    op.drop_column("devices", "auth_issued_at")
