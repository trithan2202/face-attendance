"""Normalise employee departments into their own table."""

from alembic import op
import sqlalchemy as sa


revision = "20260813_0004"
down_revision = "20260813_0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("manager_name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_departments_code", "departments", ["code"])

    op.add_column(
        "employees", sa.Column("department_id", sa.Integer(), nullable=True)
    )
    op.create_index(
        "ix_employees_department_id", "employees", ["department_id"]
    )
    op.create_foreign_key(
        "fk_employees_department_id",
        "employees",
        "departments",
        ["department_id"],
        ["id"],
    )

    # Carry the existing free-text values over. The code is derived from the
    # name so the seeded departments stay recognisable; collisions are avoided
    # by appending the row number.
    op.execute(
        """
        INSERT INTO departments (code, name, created_at, updated_at)
        SELECT
            UPPER(
                LEFT(
                    REGEXP_REPLACE(TRIM(department), '[^A-Za-z0-9]+', '_', 'g'),
                    40
                )
            ) || '_' || ROW_NUMBER() OVER (ORDER BY TRIM(department)),
            TRIM(department),
            NOW(),
            NOW()
        FROM (
            SELECT DISTINCT TRIM(department) AS department
            FROM employees
            WHERE department IS NOT NULL AND TRIM(department) <> ''
        ) AS distinct_departments
        """
    )
    op.execute(
        """
        UPDATE employees
        SET department_id = departments.id
        FROM departments
        WHERE TRIM(employees.department) = departments.name
        """
    )

    op.drop_column("employees", "department")


def downgrade():
    op.add_column(
        "employees", sa.Column("department", sa.String(255), nullable=True)
    )
    op.execute(
        """
        UPDATE employees
        SET department = departments.name
        FROM departments
        WHERE employees.department_id = departments.id
        """
    )
    op.drop_constraint(
        "fk_employees_department_id", "employees", type_="foreignkey"
    )
    op.drop_index("ix_employees_department_id", table_name="employees")
    op.drop_column("employees", "department_id")
    op.drop_table("departments")
