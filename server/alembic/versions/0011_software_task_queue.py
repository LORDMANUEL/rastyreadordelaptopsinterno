"""device software task queue

Revision ID: 0011_software_task_queue
Revises: 0010_offline_observability
"""

from alembic import op
import sqlalchemy as sa

revision = "0011_software_task_queue"
down_revision = "0010_offline_observability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "device_software_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("device_id", sa.String(length=36), nullable=False),
        sa.Column("catalog_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_detail", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_device_software_tasks_device_id", "device_software_tasks", ["device_id"])
    op.create_index("ix_device_software_tasks_catalog_id", "device_software_tasks", ["catalog_id"])
    op.create_index("ix_device_software_tasks_action", "device_software_tasks", ["action"])
    op.create_index("ix_device_software_tasks_status", "device_software_tasks", ["status"])


def downgrade() -> None:
    op.drop_index("ix_device_software_tasks_status", table_name="device_software_tasks")
    op.drop_index("ix_device_software_tasks_action", table_name="device_software_tasks")
    op.drop_index("ix_device_software_tasks_catalog_id", table_name="device_software_tasks")
    op.drop_index("ix_device_software_tasks_device_id", table_name="device_software_tasks")
    op.drop_table("device_software_tasks")
