from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class AttendanceEvent(Base):
    __tablename__ = "attendance_events"

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

    event_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    recognized_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )

    similarity: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    detection_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    recognition_method: Mapped[str] = mapped_column(
        String(50),
        default="INSIGHTFACE",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )