"""Profitability including consumed materials — R1 extended with feed cost.

Per asset, folds the average-cost value of the feed it consumed (plus its direct
expense events) against its income, in the farm's single default currency.
Income/expense in any other currency is excluded and flagged. Read-only.

MATERIAL assets are excluded: a material purchase books an expense on the
material asset, and that same spend is re-attributed to the consumer as feed
cost — including the material asset would double-count the feed. Its consumers
(animals/crops) carry the cost instead.
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
from ovejitas.features.report.feed_cost import farm_default_currency, feed_cost_by_consumer
from ovejitas.features.report.schemas_profitability import (
    ProfitabilityFullQuery,
    ProfitabilityFullReport,
    ProfitabilityFullRow,
    ProfitabilityFullTotal,
)


async def _financials(
    db: AsyncSession, farm_id: int, q: ProfitabilityFullQuery, currency: str
) -> tuple[dict[int, Decimal], dict[int, Decimal], set[int]]:
    """Per-asset income and direct expense in the farm currency, plus the assets
    that also had income/expense in some other currency (excluded from totals)."""
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

    inc_by_asset: dict[int, Decimal] = defaultdict(lambda: Decimal(0))
    exp_by_asset: dict[int, Decimal] = defaultdict(lambda: Decimal(0))
    other_currency: set[int] = set()
    for asset_id, cur, inc, exp in (await db.execute(stmt)).all():
        if cur == currency:
            inc_by_asset[asset_id] += Decimal(inc)
            exp_by_asset[asset_id] += Decimal(exp)
        elif inc or exp:
            other_currency.add(asset_id)
    return dict(inc_by_asset), dict(exp_by_asset), other_currency


async def _asset_names(db: AsyncSession, farm_id: int, ids: set[int]) -> dict[int, str]:
    if not ids:
        return {}
    stmt = select(Asset.id, Asset.name).where(Asset.farm_id == farm_id, Asset.id.in_(ids))
    return {aid: name for aid, name in (await db.execute(stmt)).all()}


def _totals(rows: list[ProfitabilityFullRow], currency: str) -> list[ProfitabilityFullTotal]:
    if not rows:
        return []
    agg = {
        "income_total": Decimal(0),
        "direct_expense_total": Decimal(0),
        "consumed_material_cost": Decimal(0),
        "total_cost": Decimal(0),
        "net": Decimal(0),
        "net_incl_materials": Decimal(0),
    }
    for r in rows:
        agg["income_total"] += r.income_total
        agg["direct_expense_total"] += r.direct_expense_total
        agg["consumed_material_cost"] += r.consumed_material_cost
        agg["total_cost"] += r.total_cost
        agg["net"] += r.net
        agg["net_incl_materials"] += r.net_incl_materials
    return [ProfitabilityFullTotal(currency=currency, **agg)]


async def profitability_full(
    db: AsyncSession, farm_id: int, q: ProfitabilityFullQuery
) -> ProfitabilityFullReport:
    currency = await farm_default_currency(db, farm_id)
    income, expense, other_currency = await _financials(db, farm_id, q, currency)

    consumer_ids = {q.asset_id} if q.asset_id is not None else None
    feed_cost, unvalued = await feed_cost_by_consumer(
        db, farm_id, currency, consumer_ids, q.date_from, q.date_to
    )

    ids = set(income) | set(expense) | other_currency | set(feed_cost) | unvalued
    names = await _asset_names(db, farm_id, ids)

    rows: list[ProfitabilityFullRow] = []
    for asset_id in sorted(ids, key=lambda i: (names.get(i, ""), i)):
        inc = income.get(asset_id, Decimal(0))
        direct = expense.get(asset_id, Decimal(0))
        consumed = feed_cost.get(asset_id, Decimal(0))
        total = direct + consumed
        rows.append(
            ProfitabilityFullRow(
                asset_id=asset_id,
                asset_name=names.get(asset_id, ""),
                currency=currency,
                income_total=inc,
                direct_expense_total=direct,
                consumed_material_cost=consumed,
                total_cost=total,
                net=inc - direct,
                net_incl_materials=inc - total,
                has_unvalued_consumption=asset_id in unvalued,
                has_other_currency=asset_id in other_currency,
            )
        )
    return ProfitabilityFullReport(data=rows, totals=_totals(rows, currency))
