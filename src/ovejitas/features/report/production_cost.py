"""R3 replacement — cost per produced unit, attributed to the producer asset.

A producer is any asset that records ``production`` events. Its cost per unit is
``(direct expense events on it + the average-cost value of the feed it was fed)
/ its production quantity``, computed per (producer, currency): direct expense
and feed are never summed across currencies, so a producer with costs in two
currencies yields two rows. Read-only; computed live, no persistence.
"""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.filters import apply_date_range
from ovejitas.features.asset.models import Asset
from ovejitas.features.currency.models import Currency
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.report.feed_cost import feed_cost_by_consumer
from ovejitas.features.report.schemas import CostPerUnitQuery, CostPerUnitReport, CostPerUnitRow


async def _producers(db: AsyncSession, farm_id: int, q: CostPerUnitQuery) -> dict[int, str]:
    stmt = (
        select(Asset.id, Asset.name)
        .join(Event, Event.asset_id == Asset.id)
        .where(Asset.farm_id == farm_id, Event.type == EventType.PRODUCTION, Event.unit == q.unit)
        .distinct()
    )
    if q.asset_id is not None:
        stmt = stmt.where(Asset.id == q.asset_id)
    return {aid: name for aid, name in (await db.execute(stmt)).all()}


async def _production(db: AsyncSession, ids: set[int], q: CostPerUnitQuery) -> dict[int, Decimal]:
    stmt = (
        select(Event.asset_id, func.sum(Event.quantity))
        .where(
            Event.type == EventType.PRODUCTION,
            Event.unit == q.unit,
            Event.asset_id.in_(ids),
            Event.quantity.is_not(None),
        )
        .group_by(Event.asset_id)
    )
    stmt = apply_date_range(stmt, Event.occurred_at, q.date_from, q.date_to)
    return {aid: Decimal(qty) for aid, qty in (await db.execute(stmt)).all()}


async def _direct_expense(
    db: AsyncSession, ids: set[int], q: CostPerUnitQuery
) -> dict[tuple[int, str], Decimal]:
    """Direct expense per (producer, currency) — currencies stay separate."""
    stmt = (
        select(Event.asset_id, Currency.code, func.sum(Event.amount))
        .join(Currency, Currency.id == Event.currency_id)
        .where(
            Event.type == EventType.EXPENSE,
            Event.asset_id.in_(ids),
            Event.amount.is_not(None),
            Event.currency_id.is_not(None),
        )
        .group_by(Event.asset_id, Currency.code)
    )
    stmt = apply_date_range(stmt, Event.occurred_at, q.date_from, q.date_to)
    return {(aid, cur): Decimal(amt) for aid, cur, amt in (await db.execute(stmt)).all()}


def _row(
    asset_id: int,
    currency: str | None,
    name: str,
    produced: Decimal,
    direct: Decimal,
    consumed: Decimal,
    unvalued: bool,
) -> CostPerUnitRow:
    total = direct + consumed
    return CostPerUnitRow(
        asset_id=asset_id,
        asset_name=name,
        currency=currency,
        production_quantity=produced,
        direct_expense_total=direct,
        consumed_material_cost=consumed,
        total_cost=total,
        cost_per_unit=(
            (total / produced).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if produced > 0
            else None
        ),
        has_unvalued_consumption=unvalued,
    )


async def production_cost(db: AsyncSession, farm_id: int, q: CostPerUnitQuery) -> CostPerUnitReport:
    producers = await _producers(db, farm_id, q)
    if not producers:
        return CostPerUnitReport(data=[], unit=q.unit)
    ids = set(producers)

    production = await _production(db, ids, q)
    direct = await _direct_expense(db, ids, q)
    feed_cost, unvalued = await feed_cost_by_consumer(db, farm_id, ids, q.date_from, q.date_to)

    keys = set(direct) | set(feed_cost)
    rows = [
        _row(
            aid,
            cur,
            producers[aid],
            production.get(aid, Decimal(0)),
            direct.get((aid, cur), Decimal(0)),
            feed_cost.get((aid, cur), Decimal(0)),
            aid in unvalued,
        )
        for aid, cur in keys
    ]
    # a producer with no cost in any currency still reports its (zero) cost
    priced = {aid for aid, _ in keys}
    rows += [
        _row(
            aid,
            None,
            name,
            production.get(aid, Decimal(0)),
            Decimal(0),
            Decimal(0),
            aid in unvalued,
        )
        for aid, name in producers.items()
        if aid not in priced
    ]
    rows.sort(key=lambda r: (r.asset_name, r.asset_id, r.currency or ""))
    return CostPerUnitReport(data=rows, unit=q.unit)
