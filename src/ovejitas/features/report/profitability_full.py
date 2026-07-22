"""Profitability including consumed materials — R1 extended with feed cost.

Per (asset, currency), folds the average-cost value of the feed it consumed (plus
its direct expense events) against its income. Like R1, one row per (asset,
currency): amounts in different currencies are never summed or converted. Feed is
valued in the currency of the purchases backing it. Read-only.

MATERIAL assets are excluded: a material purchase books an expense on the
material asset, and that same spend is re-attributed to the consumer as feed
cost — including the material asset would double-count the feed. Its consumers
(animals/crops) carry the cost instead.

That exclusion is also why produce income has to be allocated back here. Selling
a pooled produce asset books its income on the produce asset — a MATERIAL, so
invisible to this report — leaving the animals that made it showing every cost
and none of the revenue. ``allocated_produce_income`` closes that loop, and
cannot double-count for the same reason: the pool's own income row is excluded.
"""

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.filters import apply_date_range
from ovejitas.features.asset.models import Asset, AssetKind
from ovejitas.features.currency.models import Currency
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.report.feed_cost import feed_cost_by_consumer
from ovejitas.features.report.produce_income import (
    allocations_for_farm,
    income_by_producer_currency,
)
from ovejitas.features.report.schemas_profitability import (
    ProfitabilityFullQuery,
    ProfitabilityFullReport,
    ProfitabilityFullRow,
    ProfitabilityFullTotal,
)

Financials = dict[tuple[int, str], tuple[Decimal, Decimal]]


async def _financials(db: AsyncSession, farm_id: int, q: ProfitabilityFullQuery) -> Financials:
    """Income and direct expense per (asset, currency). Currency is a live group
    dimension, so an asset with events in two currencies yields two entries."""
    income = func.coalesce(
        func.sum(case((Event.type == EventType.INCOME, Event.amount), else_=0)), 0
    )
    expense = func.coalesce(
        func.sum(case((Event.type == EventType.EXPENSE, Event.amount), else_=0)), 0
    )
    stmt = (
        select(Event.asset_id, Currency.code, income, expense)
        .join(Asset, Asset.id == Event.asset_id)
        .join(Currency, Currency.id == Event.currency_id)
        .where(
            Asset.farm_id == farm_id,
            Asset.kind != AssetKind.MATERIAL,
            Event.type.in_([EventType.INCOME, EventType.EXPENSE]),
            Event.amount.is_not(None),
            Event.currency_id.is_not(None),
        )
        .group_by(Event.asset_id, Currency.code)
    )
    stmt = apply_date_range(stmt, Event.occurred_at, q.date_from, q.date_to)
    if q.asset_id is not None:
        stmt = stmt.where(Event.asset_id == q.asset_id)
    return {
        (asset_id, cur): (Decimal(inc), Decimal(exp))
        for asset_id, cur, inc, exp in (await db.execute(stmt)).all()
    }


async def _asset_names(db: AsyncSession, farm_id: int, ids: set[int]) -> dict[int, str]:
    if not ids:
        return {}
    stmt = select(Asset.id, Asset.name).where(Asset.farm_id == farm_id, Asset.id.in_(ids))
    return {aid: name for aid, name in (await db.execute(stmt)).all()}


def _row(
    asset_id: int,
    currency: str | None,
    name: str,
    income: Decimal,
    direct: Decimal,
    consumed: Decimal,
    allocated: Decimal,
    unvalued: bool,
) -> ProfitabilityFullRow:
    total = direct + consumed
    return ProfitabilityFullRow(
        asset_id=asset_id,
        asset_name=name,
        currency=currency,
        income_total=income,
        allocated_produce_income=allocated,
        direct_expense_total=direct,
        consumed_material_cost=consumed,
        total_cost=total,
        net=income - direct,
        net_incl_materials=income + allocated - total,
        has_unvalued_consumption=unvalued,
    )


def _totals(rows: list[ProfitabilityFullRow]) -> list[ProfitabilityFullTotal]:
    fields = (
        "income_total",
        "allocated_produce_income",
        "direct_expense_total",
        "consumed_material_cost",
        "total_cost",
        "net",
        "net_incl_materials",
    )
    agg: dict[str, dict[str, Decimal]] = defaultdict(lambda: {f: Decimal(0) for f in fields})
    for r in rows:
        if r.currency is None:
            continue
        for f in fields:
            agg[r.currency][f] += getattr(r, f)
    return [ProfitabilityFullTotal(currency=cur, **agg[cur]) for cur in sorted(agg)]


async def profitability_full(
    db: AsyncSession, farm_id: int, q: ProfitabilityFullQuery
) -> ProfitabilityFullReport:
    financials = await _financials(db, farm_id, q)
    consumer_ids = {q.asset_id} if q.asset_id is not None else None
    feed_cost, unvalued = await feed_cost_by_consumer(
        db, farm_id, consumer_ids, q.date_from, q.date_to
    )
    allocated = income_by_producer_currency(
        await allocations_for_farm(db, farm_id), q.date_from, q.date_to
    )
    if q.asset_id is not None:
        allocated = {k: v for k, v in allocated.items() if k[0] == q.asset_id}

    keys = set(financials) | set(feed_cost) | set(allocated)
    priced_assets = {aid for aid, _ in keys}
    # an asset whose only activity is unvalued feed has no currency anywhere; it
    # still surfaces once so its missing feed cost is not silently dropped
    pure_unvalued = {aid for aid in unvalued if aid not in priced_assets}
    names = await _asset_names(db, farm_id, priced_assets | pure_unvalued)

    rows = [
        _row(
            asset_id,
            currency,
            names.get(asset_id, ""),
            *financials.get((asset_id, currency), (Decimal(0), Decimal(0))),
            feed_cost.get((asset_id, currency), Decimal(0)),
            allocated.get((asset_id, currency), Decimal(0)),
            asset_id in unvalued,
        )
        for asset_id, currency in keys
    ]
    rows += [
        _row(
            asset_id,
            None,
            names.get(asset_id, ""),
            Decimal(0),
            Decimal(0),
            Decimal(0),
            Decimal(0),
            True,
        )
        for asset_id in pure_unvalued
    ]
    rows.sort(key=lambda r: (r.asset_name, r.asset_id, r.currency or ""))
    return ProfitabilityFullReport(data=rows, totals=_totals(rows))
