"""Create initial face attendance schema."""

from alembic import op
import sqlalchemy as sa


revision = "20260813_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shifts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("late_grace_minutes", sa.Integer(), nullable=False),
        sa.Column("early_leave_grace_minutes", sa.Integer(), nullable=False),
        sa.Column("cross_day", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_shifts_code", "shifts", ["code"])

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_code", sa.String(50), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("shift_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["shift_id"], ["shifts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_code"),
    )
    op.create_index("ix_employees_employee_code", "employees", ["employee_code"])
    op.create_index("ix_employees_shift_id", "employees", ["shift_id"])

    op.create_table(
        "attendance_daily",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("shift_id", sa.Integer(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("first_check_in", sa.DateTime(), nullable=True),
        sa.Column("last_check_out", sa.DateTime(), nullable=True),
        sa.Column("worked_minutes", sa.Integer(), nullable=False),
        sa.Column("late_minutes", sa.Integer(), nullable=False),
        sa.Column("early_leave_minutes", sa.Integer(), nullable=False),
        sa.Column("overtime_minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("is_late", sa.Boolean(), nullable=False),
        sa.Column("is_early_leave", sa.Boolean(), nullable=False),
        sa.Column("is_overtime", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shift_id"], ["shifts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "employee_id", "work_date", name="uq_attendance_daily_employee_work_date"
        ),
    )
    op.create_index("ix_attendance_daily_employee_id", "attendance_daily", ["employee_id"])
    op.create_index("ix_attendance_daily_work_date", "attendance_daily", ["work_date"])

    op.create_table(
        "attendance_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("recognized_at", sa.DateTime(), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column("detection_score", sa.Float(), nullable=True),
        sa.Column("recognition_method", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attendance_events_employee_id", "attendance_events", ["employee_id"])
    op.create_index("ix_attendance_events_recognized_at", "attendance_events", ["recognized_at"])

    op.create_table(
        "face_embeddings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("embedding", sa.LargeBinary(), nullable=False),
        sa.Column("sample_index", sa.Integer(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("detection_score", sa.Float(), nullable=True),
        sa.Column("is_centroid", sa.Boolean(), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_face_embeddings_employee_id", "face_embeddings", ["employee_id"])
    op.create_index("ix_face_embeddings_is_centroid", "face_embeddings", ["is_centroid"])


def downgrade():
    op.drop_table("face_embeddings")
    op.drop_table("attendance_events")
    op.drop_table("attendance_daily")
    op.drop_table("employees")
    op.drop_table("shifts")
