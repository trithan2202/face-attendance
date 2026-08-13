from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

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

    embedding: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False
    )

    sample_index: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    quality_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    detection_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    is_centroid: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        default="buffalo_l",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    employee = relationship(
        "Employee",
        back_populates="embeddings"
    )