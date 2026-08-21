"""Add leave requests raised and approved by admins."""

from alembic import op
import sqlalchemy as sa


revision = "20260813_0005"
down_revision = "20260813_0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "leave_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("leave_type", sa.String(30), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_by_admin_id", sa.Integer(), nullable=False),
        sa.Column("decided_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decision_note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["employee_id"], ["employees.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by_admin_id"], ["admin_users.id"]),
        sa.ForeignKeyConstraint(["decided_by_admin_id"], ["admin_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_leave_requests_employee_id", "leave_requests", ["employee_id"]
    )
    op.create_index(
        "ix_leave_requests_start_date", "leave_requests", ["start_date"]
    )
    op.create_index(
        "ix_leave_requests_created_by_admin_id",
        "leave_requests",
        ["created_by_admin_id"],
    )


def downgrade():
    op.drop_table("leave_requests")
