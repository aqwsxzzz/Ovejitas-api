from datetime import date
from enum import StrEnum
from typing import Any

from sqlalchemy import Date, ForeignKey, Identity, Index, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ovejitas.core.models import Base, TimestampMixin


class IndividualStatus(StrEnum):
    ACTIVE = "active"
    SOLD = "sold"
    DECEASED = "deceased"
    ARCHIVED = "archived"


class Individual(Base, TimestampMixin):
    __tablename__ = "individual"
    __table_args__ = (Index("ix_individual_farm_status", "farm_id", "status"),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farm.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tag: Mapped[str] = mapped_column(String(128), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    mother_id: Mapped[int | None] = mapped_column(
        ForeignKey("individual.id", ondelete="SET NULL"),
        nullable=True,
    )
    father_id: Mapped[int | None] = mapped_column(
        ForeignKey("individual.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[IndividualStatus] = mapped_column(
        SQLEnum(
            IndividualStatus,
            name="individual_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=IndividualStatus.ACTIVE,
    )
    # Paired events emitted by the acquisition flow. Nullable at the schema
    # level — the service is the single writer and always sets the acquisition
    # event; the expense event exists only for purchased acquisitions.
    acquisition_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("event.id", ondelete="RESTRICT"),
        nullable=True,
        unique=True,
    )
    acquisition_expense_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("event.id", ondelete="RESTRICT"),
        nullable=True,
        unique=True,
    )
    # Set by the mortality flow when status transitions to ``deceased``;
    # cleared when that transition is reversed.
    mortality_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("event.id", ondelete="RESTRICT"),
        nullable=True,
        unique=True,
    )
    # Set by the sale flow when status transitions to ``sold``;
    # cleared when that transition is reversed.
    sale_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("event.id", ondelete="RESTRICT"),
        nullable=True,
        unique=True,
    )
    extra: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )
