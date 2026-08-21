"""Add the national ID (CCCD) used for employee self-service lookups."""

from alembic import op
import sqlalchemy as sa


revision = "20260813_0008"
down_revision = "20260813_0007"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "employees", sa.Column("national_id", sa.String(20), nullable=True)
    )
    op.create_index(
        "ix_employees_national_id", "employees", ["national_id"]
    )


def downgrade():
    op.drop_index("ix_employees_national_id", table_name="employees")
    op.drop_column("employees", "national_id")
