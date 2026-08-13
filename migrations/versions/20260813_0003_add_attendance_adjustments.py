"""Add audit records for attendance adjustments."""

from alembic import op
import sqlalchemy as sa


revision = "20260813_0003"
down_revision = "20260813_0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "attendance_adjustments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attendance_daily_id", sa.Integer(), nullable=False),
        sa.Column("admin_user_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("before_data", sa.JSON(), nullable=False),
        sa.Column("after_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["attendance_daily_id"], ["attendance_daily.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["admin_user_id"], ["admin_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_attendance_adjustments_attendance_daily_id",
        "attendance_adjustments",
        ["attendance_daily_id"],
    )
    op.create_index(
        "ix_attendance_adjustments_admin_user_id",
        "attendance_adjustments",
        ["admin_user_id"],
    )
    op.create_index(
        "ix_attendance_adjustments_created_at",
        "attendance_adjustments",
        ["created_at"],
    )


def downgrade():
    op.drop_table("attendance_adjustments")
