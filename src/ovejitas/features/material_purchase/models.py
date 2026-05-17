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


class MaterialPurchase(Base, TimestampMixin):
    """A material entering stock via purchase, with the cost paid.

    Each row owns two paired events — an INVENTORY ``increment`` and an
    ``expense`` — that keep the event-sourced stock balance and the finance
    ledger consistent.
    """

    __tablename__ = "material_purchase"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_material_purchase_farm_occurred", "farm_id", "occurred_at"),
        Index(
            "ix_material_purchase_material_occurred",
            "farm_id",
            "material_asset_id",
            "occurred_at",
        ),
        Index(
            "uq_material_purchase_farm_idempotency_key",
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
    inventory_event_id: Mapped[int] = mapped_column(
        ForeignKey("event.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    expense_event_id: Mapped[int] = mapped_column(
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
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    supplier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        nullable=False,
    )
