"""Shared feed-cost basis for the cost reports.

Values the feed a consumer asset was fed at the *average purchase cost* of the
material, **per currency of the backing purchases**. A material may be bought in
several currencies; its cost basis is therefore per-currency, and consuming it
splits the cost across those currencies in proportion to the quantity purchased
in each — amounts are never summed or converted across currencies. Used by both
the cost-per-unit report (R3) and the profitability-full report so the two can
never disagree.
"""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.filters import apply_date_range
from ovejitas.features.currency.models import Currency
from ovejitas.features.material_consumption.models import MaterialConsumption
from ovejitas.features.material_consumption.types import ConsumptionReason
from ovejitas.features.material_purchase.models import MaterialPurchase

# Per material: total quantity purchased across all currencies, and spend keyed
# by currency code. The split rule divides consumed quantity by the total and
# multiplies each currency's spend, so amounts in different currencies stay
# separate.
MaterialBasis = tuple[Decimal, dict[str, Decimal]]


async def _material_basis(
    db: AsyncSession,
    farm_id: int,
    material_ids: set[int],
    date_to: datetime | None,
) -> dict[int, MaterialBasis]:
    """Purchase basis per material over full history up to ``date_to``:
    ``{material_id: (total_qty_all_currencies, {currency_code: spend})}``.
    Purchases in different currencies are grouped separately, never summed."""
    if not material_ids:
        return {}
    stmt = (
        select(
            MaterialPurchase.material_asset_id,
            Currency.code,
            func.sum(MaterialPurchase.amount),
            func.sum(MaterialPurchase.quantity),
        )
        .join(Currency, Currency.id == MaterialPurchase.currency_id)
        .where(
            MaterialPurchase.farm_id == farm_id,
            MaterialPurchase.material_asset_id.in_(material_ids),
        )
        .group_by(MaterialPurchase.material_asset_id, Currency.code)
    )
    stmt = apply_date_range(stmt, MaterialPurchase.occurred_at, None, date_to)
    spend: dict[int, dict[str, Decimal]] = defaultdict(dict)
    total_qty: dict[int, Decimal] = defaultdict(lambda: Decimal(0))
    for material_id, code, amount, qty in (await db.execute(stmt)).all():
        spend[material_id][code] = Decimal(amount)
        total_qty[material_id] += Decimal(qty)
    return {mid: (total_qty[mid], spend[mid]) for mid in spend}


async def feed_cost_by_consumer(
    db: AsyncSession,
    farm_id: int,
    consumer_ids: set[int] | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> tuple[dict[tuple[int, str], Decimal], set[int]]:
    """Feed cost per ``(consumer asset, currency)`` within ``[date_from, date_to]``.

    Returns ``(feed_cost_by_consumer_and_currency, unvalued_consumer_ids)``. Feed
    is ``material_consumption`` with ``reason=feeding``. Consuming ``qty`` of a
    material generates cost in each currency the material was purchased in,
    apportioned by that currency's share of purchased quantity —
    ``cost_c = qty * spend_c / total_purchased_qty`` — so nothing is summed or
    converted across currencies. A consumer is flagged unvalued only when feed it
    consumed has **no** purchase basis in **any** currency. When ``consumer_ids``
    is ``None`` every feeding consumer in the farm is included.
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

    basis = await _material_basis(db, farm_id, {mid for _, mid, _ in consumption}, date_to)
    feed_cost: dict[tuple[int, str], Decimal] = defaultdict(lambda: Decimal(0))
    unvalued: set[int] = set()
    for consumer_id, material_id, qty in consumption:
        priced = basis.get(material_id)
        if priced is None or priced[0] <= 0:
            unvalued.add(consumer_id)
            continue
        total_qty, spend_by_currency = priced
        for code, spend in spend_by_currency.items():
            feed_cost[(consumer_id, code)] += Decimal(qty) * spend / total_qty
    return dict(feed_cost), unvalued
