"""R3 replacement — cost per produced unit, attributed to the producer asset.

A producer is any asset that records ``production`` events. Its cost per unit
is ``(direct expense events on it + the average-cost value of the feed it was
fed) / its production quantity``. Read-only; computed live, no persistence.
"""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.filters import apply_date_range
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.report.feed_cost import farm_default_currency, feed_cost_by_consumer
from ovejitas.features.report.schemas import CostPerUnitQuery, CostPerUnitReport, CostPerUnitRow


async def production_cost(db: AsyncSession, farm_id: int, q: CostPerUnitQuery) -> CostPerUnitReport:
    currency = await farm_default_currency(db, farm_id)

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

    feed_cost, unvalued = await feed_cost_by_consumer(
        db, farm_id, currency, ids, q.date_from, q.date_to
    )

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
