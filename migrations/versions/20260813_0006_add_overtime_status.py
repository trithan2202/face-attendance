"""Add an approval state to overtime recorded on a work day."""

from alembic import op
import sqlalchemy as sa


revision = "20260813_0006"
down_revision = "20260813_0005"
branch_labels = None
depends_on = None


def upgrade():
    # Added nullable first so existing rows can be backfilled; the codebase does
    # not use server defaults, so the column is tightened afterwards.
    op.add_column(
        "attendance_daily",
        sa.Column("overtime_status", sa.String(20), nullable=True),
    )
    op.execute(
        """
        UPDATE attendance_daily
        SET overtime_status = CASE
            WHEN overtime_minutes > 0 THEN 'PENDING'
            ELSE 'NONE'
        END
        """
    )
    op.alter_column("attendance_daily", "overtime_status", nullable=False)


def downgrade():
    op.drop_column("attendance_daily", "overtime_status")
