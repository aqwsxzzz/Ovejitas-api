from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Identity, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ovejitas.core.models import Base, TimestampMixin


class Currency(Base, TimestampMixin):
    __tablename__ = "currency"
    __table_args__ = (UniqueConstraint("farm_id", "code", name="farm_code"),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farm.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # ISO 4217 code, frozen after creation so historical events referencing this
    # currency always read with the code they were booked in.
    code: Mapped[str] = mapped_column(String(3), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(8), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
