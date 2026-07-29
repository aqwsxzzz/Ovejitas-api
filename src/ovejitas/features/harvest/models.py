"""The produce lot — one producer's contribution to a produce asset's pool.

A harvest deposits output from one producer into a shared produce asset, and
once deposited the goods are fungible: eggs from three coops in one basket are
indistinguishable. The two events a harvest emits (PRODUCTION on the producer,
INVENTORY increment on the pool) carry no link to each other, so nothing in the
event stream records *who* contributed what to the pool. This row is that link.

It is what makes per-producer revenue attribution derivable: the FIFO engine
reads lots oldest-first and splits each outflow proportionally across the
contributors of the lot it draws from. Lots on the same calendar day form one
basket, so the order of same-day harvests never changes anyone's share.

Mirrors the material_purchase sidecar: one row owning the paired events it was
emitted with, RESTRICT so neither event can vanish under it.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Identity, Index, Numeric
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from ovejitas.core.models import Base, TimestampMixin
from ovejitas.features.event.types import Unit


class ProduceLot(Base, TimestampMixin):
    __tablename__ = "produce_lot"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint(
            "produce_asset_id <> producer_asset_id",
            name="producer_is_not_pool",
        ),
        # The FIFO scan: equality on the pool, then oldest-first. id breaks ties
        # so two lots at the same instant still have a total order.
        Index(
            "ix_produce_lot_pool_occurred",
            "produce_asset_id",
            "occurred_at",
            "id",
        ),
        Index("ix_produce_lot_producer_occurred", "producer_asset_id", "occurred_at"),
        Index("ix_produce_lot_farm_occurred", "farm_id", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farm.id", ondelete="CASCADE"),
        nullable=False,
    )
    # The pool this lot was deposited into.
    produce_asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # The animal or crop asset that produced it — the whole point of the row.
    producer_asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id", ondelete="RESTRICT"),
        nullable=False,
    )
    production_event_id: Mapped[int] = mapped_column(
        ForeignKey("event.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
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
    created_by: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        nullable=False,
    )
