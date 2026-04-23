from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Identity, String, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from ovejitas.core.models import Base, TimestampMixin
from ovejitas.features.event.types import EventType


class EventCategory(Base, TimestampMixin):
    __tablename__ = "event_category"
    __table_args__ = (UniqueConstraint("farm_id", "type", "name", name="farm_type_name"),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farm.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[EventType] = mapped_column(
        SQLEnum(EventType, name="event_type", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
