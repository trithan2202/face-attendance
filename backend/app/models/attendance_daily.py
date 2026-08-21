from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class AttendanceDaily(Base):
    __tablename__ = "attendance_daily"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "work_date",
            name="uq_attendance_daily_employee_work_date"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey(
            "employees.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    shift_id: Mapped[int] = mapped_column(
        ForeignKey("shifts.id"),
        nullable=False
    )

    work_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )

    first_check_in: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    last_check_out: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    worked_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    late_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    early_leave_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    overtime_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    overtime_status: Mapped[str] = mapped_column(
        String(20),
        default="NONE",
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    is_late: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    is_early_leave: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    is_overtime: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )