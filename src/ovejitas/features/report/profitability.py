"""R1 profitability — income minus expense per (asset, currency).

One row per (asset, currency): amounts in different currencies are never summed
or converted. Events with a NULL amount or currency are excluded. Read-only.
"""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.filters import apply_date_range
from ovejitas.features.asset.models import Asset
from ovejitas.features.currency.models import Currency
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.report.schemas_profitability import (
    ProfitabilityQuery,
    ProfitabilityRow,
    ProfitabilityTotal,
)


def _totals(rows: list[ProfitabilityRow]) -> list[ProfitabilityTotal]:
    by_currency: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"income_total": Decimal(0), "expense_total": Decimal(0), "net": Decimal(0)}
    )
    for r in rows:
        bucket = by_currency[r.currency]
        bucket["income_total"] += r.income_total
        bucket["expense_total"] += r.expense_total
        bucket["net"] += r.net
    return [ProfitabilityTotal(currency=cur, **vals) for cur, vals in sorted(by_currency.items())]


def _scope(
    stmt: Select[Any],
    farm_id: int,
    date_from: datetime | None,
    date_to: datetime | None,
    asset_id: int | None = None,
) -> Select[Any]:
    stmt = stmt.where(Event.farm_id == farm_id)
    stmt = apply_date_range(stmt, Event.occurred_at, date_from, date_to)
    if asset_id is not None:
        stmt = stmt.where(Event.asset_id == asset_id)
    return stmt


async def profitability(
    db: AsyncSession, farm_id: int, q: ProfitabilityQuery
) -> tuple[list[ProfitabilityRow], list[ProfitabilityTotal]]:
    income = func.coalesce(
        func.sum(case((Event.type == EventType.INCOME, Event.amount), else_=0)), 0
    )
    expense = func.coalesce(
        func.sum(case((Event.type == EventType.EXPENSE, Event.amount), else_=0)), 0
    )
    stmt = (
        select(
            Asset.id.label("asset_id"),
            Asset.name.label("asset_name"),
            Currency.code.label("currency"),
            income.label("income_total"),
            expense.label("expense_total"),
            (income - expense).label("net"),
        )
        .join(Asset, Asset.id == Event.asset_id)
        .join(Currency, Currency.id == Event.currency_id)
        .where(
            Asset.farm_id == farm_id,
            Event.type.in_([EventType.INCOME, EventType.EXPENSE]),
            Event.amount.is_not(None),
            Event.currency_id.is_not(None),
        )
        .group_by(Asset.id, Asset.name, Currency.code)
        .order_by(Asset.name, Currency.code)
    )
    stmt = _scope(stmt, farm_id, q.date_from, q.date_to, q.asset_id)
    rows = (await db.execute(stmt)).mappings().all()
    data = [ProfitabilityRow.model_validate(r) for r in rows]
    return data, _totals(data)
