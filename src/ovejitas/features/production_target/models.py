from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from ovejitas.core.models import Base, TimestampMixin
from ovejitas.features.production_target.types import ProductionBasis, TargetPeriod


class AssetProductionTarget(Base, TimestampMixin):
    """A per-asset, per-product expected production rate. The product is a
    production ``event_category``; ``basis`` selects how the report scales it.

    Effective-dated: a rate that changes over time is a new row with a later
    ``effective_from`` rather than an edit, so historical reports stay truthful.
    """

    __tablename__ = "asset_production_target"
    __table_args__ = (
        UniqueConstraint(
            "asset_id", "category_id", "effective_from", name="uq_target_asset_category_from"
        ),
        CheckConstraint("expected_rate >= 0", name="ck_target_rate_non_negative"),
        # period is set iff the basis is the continuous per-head one.
        CheckConstraint(
            "(basis = 'per_head_continuous') = (period IS NOT NULL)",
            name="ck_target_period_for_continuous",
        ),
        Index("ix_target_farm", "farm_id"),
        Index("ix_target_category", "category_id"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farm.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("asset.id", ondelete="CASCADE"), nullable=False
    )
    # RESTRICT: a product with targets cannot be hard-deleted out from under them.
    category_id: Mapped[int] = mapped_column(
        ForeignKey("event_category.id", ondelete="RESTRICT"), nullable=False
    )
    basis: Mapped[ProductionBasis] = mapped_column(
        SQLEnum(
            ProductionBasis,
            name="production_basis",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    expected_rate: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    period: Mapped[TargetPeriod | None] = mapped_column(
        SQLEnum(TargetPeriod, name="target_period", values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
