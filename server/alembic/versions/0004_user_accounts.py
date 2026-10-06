"""role based user accounts

Revision ID: 0004_user_accounts
Revises: 0003_device_observations
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_user_accounts"
down_revision = "0003_device_observations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("auth_salt", sa.String(length=64), nullable=False),
        sa.Column("auth_digest", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_accounts_username", "user_accounts", ["username"], unique=True)
    op.create_index("ix_user_accounts_role", "user_accounts", ["role"])
    op.create_index("ix_user_accounts_is_active", "user_accounts", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_user_accounts_is_active", table_name="user_accounts")
    op.drop_index("ix_user_accounts_role", table_name="user_accounts")
    op.drop_index("ix_user_accounts_username", table_name="user_accounts")
    op.drop_table("user_accounts")
