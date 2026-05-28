"""R3 replacement — cost per produced unit, attributed to the producer asset.

A producer is any asset that records ``production`` events. Its cost per unit
is ``(direct expense events on it + the average-cost value of the feed it was
fed) / its production quantity``. Read-only; computed live, no persistence.
"""

from collections import defaultdict
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError
from ovejitas.core.filters import apply_date_range
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.farm.models import Farm
from ovejitas.features.material_consumption.models import MaterialConsumption
from ovejitas.features.material_consumption.types import ConsumptionReason
from ovejitas.features.material_purchase.models import MaterialPurchase
from ovejitas.features.report.schemas import CostPerUnitQuery, CostPerUnitReport, CostPerUnitRow


async def _farm_currency(db: AsyncSession, farm_id: int) -> str:
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise NotFoundError("Farm not found")
    return farm.default_currency


async def _material_unit_cost(
    db: AsyncSession, farm_id: int, material_ids: set[int], date_to: datetime | None
) -> dict[int, Decimal]:
    """Average cost per unit of each material — total purchase spend over total
    quantity purchased, across the full history up to ``date_to``."""
    if not material_ids:
        return {}
    stmt = (
        select(
            MaterialPurchase.material_asset_id,
            func.sum(MaterialPurchase.amount),
            func.sum(MaterialPurchase.quantity),
        )
        .where(
            MaterialPurchase.farm_id == farm_id,
            MaterialPurchase.material_asset_id.in_(material_ids),
        )
        .group_by(MaterialPurchase.material_asset_id)
    )
    stmt = apply_date_range(stmt, MaterialPurchase.occurred_at, None, date_to)
    rows = (await db.execute(stmt)).all()
    return {mid: Decimal(amount) / Decimal(qty) for mid, amount, qty in rows if qty}


async def production_cost(db: AsyncSession, farm_id: int, q: CostPerUnitQuery) -> CostPerUnitReport:
    currency = await _farm_currency(db, farm_id)

    producer_stmt = (
        select(Asset.id, Asset.name)
        .join(Event, Event.asset_id == Asset.id)
        .where(
            Asset.farm_id == farm_id,
            Event.type == EventType.PRODUCTION,
            Event.unit == q.unit,
        )
        .distinct()
    )
    if q.asset_id is not None:
        producer_stmt = producer_stmt.where(Asset.id == q.asset_id)
    producers: dict[int, str] = {aid: name for aid, name in (await db.execute(producer_stmt)).all()}
    if not producers:
        return CostPerUnitReport(data=[], unit=q.unit)
    ids = set(producers)

    prod_stmt = (
        select(Event.asset_id, func.sum(Event.quantity))
        .where(
            Event.type == EventType.PRODUCTION,
            Event.unit == q.unit,
            Event.asset_id.in_(ids),
            Event.quantity.is_not(None),
        )
        .group_by(Event.asset_id)
    )
    prod_stmt = apply_date_range(prod_stmt, Event.occurred_at, q.date_from, q.date_to)
    production: dict[int, Decimal] = {
        aid: Decimal(qty) for aid, qty in (await db.execute(prod_stmt)).all()
    }

    exp_stmt = (
        select(Event.asset_id, func.sum(Event.amount))
        .where(
            Event.type == EventType.EXPENSE,
            Event.asset_id.in_(ids),
            Event.amount.is_not(None),
        )
        .group_by(Event.asset_id)
    )
    exp_stmt = apply_date_range(exp_stmt, Event.occurred_at, q.date_from, q.date_to)
    direct: dict[int, Decimal] = {
        aid: Decimal(amt) for aid, amt in (await db.execute(exp_stmt)).all()
    }

    cons_stmt = (
        select(
            MaterialConsumption.consumer_asset_id,
            MaterialConsumption.material_asset_id,
            func.sum(MaterialConsumption.quantity),
        )
        .where(
            MaterialConsumption.farm_id == farm_id,
            MaterialConsumption.reason == ConsumptionReason.FEEDING,
            MaterialConsumption.consumer_asset_id.in_(ids),
        )
        .group_by(
            MaterialConsumption.consumer_asset_id,
            MaterialConsumption.material_asset_id,
        )
    )
    cons_stmt = apply_date_range(cons_stmt, MaterialConsumption.occurred_at, q.date_from, q.date_to)
    consumption = (await db.execute(cons_stmt)).all()

    unit_cost = await _material_unit_cost(
        db, farm_id, {mid for _, mid, _ in consumption}, q.date_to
    )
    feed_cost: dict[int, Decimal] = defaultdict(lambda: Decimal(0))
    unvalued: set[int] = set()
    for consumer_id, material_id, qty in consumption:
        cost = unit_cost.get(material_id)
        if cost is None:
            unvalued.add(consumer_id)
        else:
            feed_cost[consumer_id] += Decimal(qty) * cost

    rows: list[CostPerUnitRow] = []
    for asset_id, name in sorted(producers.items(), key=lambda kv: kv[1]):
        produced = production.get(asset_id, Decimal(0))
        direct_total = direct.get(asset_id, Decimal(0))
        consumed = feed_cost.get(asset_id, Decimal(0))
        total = direct_total + consumed
        rows.append(
            CostPerUnitRow(
                asset_id=asset_id,
                asset_name=name,
                currency=currency,
                production_quantity=produced,
                direct_expense_total=direct_total,
                consumed_material_cost=consumed,
                total_cost=total,
                cost_per_unit=(
                    (total / produced).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    if produced > 0
                    else None
                ),
                has_unvalued_consumption=asset_id in unvalued,
            )
        )
    return CostPerUnitReport(data=rows, unit=q.unit)
