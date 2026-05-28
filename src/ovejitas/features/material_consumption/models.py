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
from ovejitas.features.event.types import Unit
from ovejitas.features.material_consumption.types import ConsumptionReason


class MaterialConsumption(Base, TimestampMixin):
    """A material leaving stock, linked to the animal/asset that consumed it.

    Each row owns a paired INVENTORY ``decrement`` event (``inventory_event_id``)
    that keeps the event-sourced stock balance consistent.
    """

    __tablename__ = "material_consumption"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint(
            "(reason = 'feeding') = (consumer_asset_id IS NOT NULL)",
            name="feeding_requires_consumer",
        ),
        CheckConstraint(
            "individual_id IS NULL OR consumer_asset_id IS NOT NULL",
            name="individual_requires_consumer",
        ),
        Index("ix_material_consumption_farm_occurred", "farm_id", "occurred_at"),
        Index(
            "ix_material_consumption_material_occurred",
            "farm_id",
            "material_asset_id",
            "occurred_at",
        ),
        Index(
            "ix_material_consumption_consumer_occurred",
            "farm_id",
            "consumer_asset_id",
            "occurred_at",
            postgresql_where=text("consumer_asset_id IS NOT NULL"),
        ),
        Index(
            "uq_material_consumption_farm_idempotency_key",
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
    material_asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id", ondelete="RESTRICT"),
        nullable=False,
    )
    consumer_asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("asset.id", ondelete="RESTRICT"),
        nullable=True,
    )
    individual_id: Mapped[int | None] = mapped_column(
        ForeignKey("individual.id", ondelete="RESTRICT"),
        nullable=True,
    )
    inventory_event_id: Mapped[int] = mapped_column(
        ForeignKey("event.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    unit: Mapped[Unit] = mapped_column(
        SQLEnum(Unit, name="unit", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    reason: Mapped[ConsumptionReason] = mapped_column(
        SQLEnum(
            ConsumptionReason,
            name="consumption_reason",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        nullable=False,
    )
