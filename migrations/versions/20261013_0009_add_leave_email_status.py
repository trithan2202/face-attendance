"""Track the approval email sent to the employee for each leave request."""

from alembic import op
import sqlalchemy as sa


revision = "20261013_0009"
down_revision = "20260813_0008"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "leave_requests",
        sa.Column(
            "email_status", sa.String(20), nullable=False, server_default="NONE"
        ),
    )
    op.add_column(
        "leave_requests", sa.Column("email_sent_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "leave_requests", sa.Column("email_error", sa.String(500), nullable=True)
    )


def downgrade():
    op.drop_column("leave_requests", "email_error")
    op.drop_column("leave_requests", "email_sent_at")
    op.drop_column("leave_requests", "email_status")
