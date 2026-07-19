from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from ovejitas.core.models import Base, TimestampMixin


class Pregnancy(Base, TimestampMixin):
    """A pregnancy/ultrasound check recorded against one individual animal.

    Each row owns a paired REPRODUCTIVE event (``reproductive_event_id``) so the
    structured projection stays connected to the individual's event timeline.
    A non-pregnant check carries no offspring count or due date.
    """

    __tablename__ = "pregnancy"
    __table_args__ = (
        CheckConstraint(
            "offspring_count IS NULL OR offspring_count >= 0",
            name="offspring_count_non_negative",
        ),
        CheckConstraint(
            "is_pregnant OR (offspring_count IS NULL AND expected_due_at IS NULL)",
            name="not_pregnant_has_no_projection",
        ),
        Index("ix_pregnancy_farm_individual", "farm_id", "individual_id"),
        Index(
            "ix_pregnancy_due",
            "farm_id",
            "expected_due_at",
            postgresql_where=text("is_pregnant AND expected_due_at IS NOT NULL"),
        ),
        Index(
            "uq_pregnancy_farm_idempotency_key",
            "farm_id",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farm.id", ondelete="CASCADE"),
        nullable=False,
    )
    individual_id: Mapped[int] = mapped_column(
        ForeignKey("individual.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reproductive_event_id: Mapped[int] = mapped_column(
        ForeignKey("event.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_pregnant: Mapped[bool] = mapped_column(Boolean, nullable=False)
    offspring_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        nullable=False,
    )
