from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AttendanceAdjustment(Base):
    __tablename__ = "attendance_adjustments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    attendance_daily_id: Mapped[int] = mapped_column(
        ForeignKey("attendance_daily.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    admin_user_id: Mapped[int] = mapped_column(
        ForeignKey("admin_users.id"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    before_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    after_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False, index=True
    )
