"""Add local administrator accounts."""

from alembic import op
import sqlalchemy as sa


revision = "20260813_0002"
down_revision = "20260813_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_admin_users_username", "admin_users", ["username"])


def downgrade():
    op.drop_table("admin_users")
