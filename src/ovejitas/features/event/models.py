from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ovejitas.core.models import Base, TimestampMixin
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit


class Event(Base, TimestampMixin):
    __tablename__ = "event"
    __table_args__ = (
        CheckConstraint(
            "type <> 'reproductive' OR individual_id IS NOT NULL",
            name="reproductive_requires_individual",
        ),
        CheckConstraint(
            "(type = 'inventory') = (adjustment IS NOT NULL)",
            name="inventory_requires_adjustment",
        ),
        Index("ix_event_farm_occurred_at", "farm_id", "occurred_at"),
        Index("ix_event_asset_type_occurred_at", "asset_id", "type", "occurred_at"),
        Index(
            "ix_event_inventory_asset_occurred",
            "asset_id",
            "occurred_at",
            postgresql_where=text("type = 'inventory'"),
        ),
        Index(
            "ix_event_individual_occurred_at",
            "individual_id",
            "occurred_at",
            postgresql_where=text("individual_id IS NOT NULL"),
        ),
        Index(
            "ix_event_category_id",
            "category_id",
            postgresql_where=text("category_id IS NOT NULL"),
        ),
        Index(
            "uq_event_farm_idempotency_key",
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
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id", ondelete="CASCADE"),
        nullable=False,
    )
    individual_id: Mapped[int | None] = mapped_column(
        ForeignKey("individual.id", ondelete="CASCADE"),
        nullable=True,
    )
    type: Mapped[EventType] = mapped_column(
        SQLEnum(EventType, name="event_type", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("event_category.id", ondelete="SET NULL"),
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    unit: Mapped[Unit | None] = mapped_column(
        SQLEnum(Unit, name="unit", values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )
    amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    adjustment: Mapped[InventoryAdjustment | None] = mapped_column(
        SQLEnum(
            InventoryAdjustment,
            name="inventory_adjustment",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=True,
    )
    currency_id: Mapped[int | None] = mapped_column(
        ForeignKey("currency.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        nullable=False,
    )
