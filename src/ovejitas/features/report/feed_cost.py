"""Shared feed-cost basis for the cost reports.

Values the feed a consumer asset was fed at the *average purchase cost* of the
material, in the farm's default currency. Used by both the cost-per-unit report
(R3) and the profitability-full report so the two can never disagree.
"""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError
from ovejitas.core.filters import apply_date_range
from ovejitas.features.currency.models import Currency
from ovejitas.features.farm.models import Farm
from ovejitas.features.material_consumption.models import MaterialConsumption
from ovejitas.features.material_consumption.types import ConsumptionReason
from ovejitas.features.material_purchase.models import MaterialPurchase


async def farm_default_currency(db: AsyncSession, farm_id: int) -> str:
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise NotFoundError("Farm not found")
    return farm.default_currency


async def _material_unit_cost(
    db: AsyncSession,
    farm_id: int,
    currency: str,
    material_ids: set[int],
    date_to: datetime | None,
) -> dict[int, Decimal]:
    """Average cost per unit of each material — purchase spend over quantity, in
    ``currency``, across the full history up to ``date_to``. Purchases in any
    other currency are excluded (amounts in different currencies are never summed
    together)."""
    if not material_ids:
        return {}
    stmt = (
        select(
            MaterialPurchase.material_asset_id,
            func.sum(MaterialPurchase.amount),
            func.sum(MaterialPurchase.quantity),
        )
        .join(Currency, Currency.id == MaterialPurchase.currency_id)
        .where(
            MaterialPurchase.farm_id == farm_id,
            MaterialPurchase.material_asset_id.in_(material_ids),
            Currency.code == currency,
        )
        .group_by(MaterialPurchase.material_asset_id)
    )
    stmt = apply_date_range(stmt, MaterialPurchase.occurred_at, None, date_to)
    rows = (await db.execute(stmt)).all()
    return {mid: Decimal(amount) / Decimal(qty) for mid, amount, qty in rows if qty}


async def feed_cost_by_consumer(
    db: AsyncSession,
    farm_id: int,
    currency: str,
    consumer_ids: set[int] | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> tuple[dict[int, Decimal], set[int]]:
    """Feed cost per consumer asset within ``[date_from, date_to]``.

    Returns ``(feed_cost_by_consumer_id, consumer_ids_whose_feed_is_unvalued)``.
    Feed is ``material_consumption`` with ``reason=feeding``; a material is
    valued at its average purchase cost in ``currency``. A consumer is flagged
    unvalued when any feed it consumed has no priceable purchase basis. When
    ``consumer_ids`` is ``None`` every feeding consumer in the farm is included.
    """
    stmt = (
        select(
            MaterialConsumption.consumer_asset_id,
            MaterialConsumption.material_asset_id,
            func.sum(MaterialConsumption.quantity),
        )
        .where(
            MaterialConsumption.farm_id == farm_id,
            MaterialConsumption.reason == ConsumptionReason.FEEDING,
        )
        .group_by(
            MaterialConsumption.consumer_asset_id,
            MaterialConsumption.material_asset_id,
        )
    )
    if consumer_ids is not None:
        stmt = stmt.where(MaterialConsumption.consumer_asset_id.in_(consumer_ids))
    stmt = apply_date_range(stmt, MaterialConsumption.occurred_at, date_from, date_to)
    consumption = (await db.execute(stmt)).all()

    unit_cost = await _material_unit_cost(
        db, farm_id, currency, {mid for _, mid, _ in consumption}, date_to
    )
    feed_cost: dict[int, Decimal] = defaultdict(lambda: Decimal(0))
    unvalued: set[int] = set()
    for consumer_id, material_id, qty in consumption:
        cost = unit_cost.get(material_id)
        if cost is None:
            unvalued.add(consumer_id)
        else:
            feed_cost[consumer_id] += Decimal(qty) * cost
    return dict(feed_cost), unvalued
