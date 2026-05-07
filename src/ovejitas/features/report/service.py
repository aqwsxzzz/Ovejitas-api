from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError
from ovejitas.core.filters import apply_date_range
from ovejitas.core.pagination import PageParams
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.individual.models import Individual
from ovejitas.features.report.schemas import (
    CostPerUnitQuery,
    CostPerUnitRow,
    CostPerUnitTotal,
    ProductionQuery,
    ProductionRow,
    ProductionTotal,
    ProfitabilityQuery,
    ProfitabilityRow,
    ProfitabilityTotal,
    TimelineQuery,
)


def _profitability_totals(rows: list[ProfitabilityRow]) -> list[ProfitabilityTotal]:
    by_currency: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"income_total": Decimal(0), "expense_total": Decimal(0), "net": Decimal(0)}
    )
    for r in rows:
        bucket = by_currency[r.currency]
        bucket["income_total"] += r.income_total
        bucket["expense_total"] += r.expense_total
        bucket["net"] += r.net
    return [ProfitabilityTotal(currency=cur, **vals) for cur, vals in sorted(by_currency.items())]


def _production_totals(rows: list[ProductionRow]) -> list[ProductionTotal]:
    by_unit: dict[Any, Decimal] = defaultdict(lambda: Decimal(0))
    for r in rows:
        by_unit[r.unit] += r.total
    return [ProductionTotal(unit=u, total=t) for u, t in sorted(by_unit.items())]


def _cost_per_unit_totals(rows: list[CostPerUnitRow]) -> list[CostPerUnitTotal]:
    by_currency: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"quantity": Decimal(0), "expense_total": Decimal(0)}
    )
    for r in rows:
        bucket = by_currency[r.currency]
        bucket["quantity"] += r.quantity
        bucket["expense_total"] += r.expense_total
    return [
        CostPerUnitTotal(
            currency=cur,
            quantity=v["quantity"],
            expense_total=v["expense_total"],
            cost_per_unit=v["expense_total"] / v["quantity"] if v["quantity"] else Decimal(0),
        )
        for cur, v in sorted(by_currency.items())
    ]


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


class ReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def profitability(
        self, farm_id: int, q: ProfitabilityQuery
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
                Event.currency.label("currency"),
                income.label("income_total"),
                expense.label("expense_total"),
                (income - expense).label("net"),
            )
            .join(Asset, Asset.id == Event.asset_id)
            .where(
                Asset.farm_id == farm_id,
                Event.type.in_([EventType.INCOME, EventType.EXPENSE]),
                Event.amount.is_not(None),
                Event.currency.is_not(None),
            )
            .group_by(Asset.id, Asset.name, Event.currency)
            .order_by(Asset.name, Event.currency)
        )
        stmt = _scope(stmt, farm_id, q.date_from, q.date_to, q.asset_id)
        rows = (await self.db.execute(stmt)).mappings().all()
        data = [ProfitabilityRow.model_validate(r) for r in rows]
        totals = _profitability_totals(data)
        return data, totals

    async def production(
        self, farm_id: int, q: ProductionQuery
    ) -> tuple[list[ProductionRow], list[ProductionTotal]]:
        bucket_col = func.date_trunc(q.bucket.value, Event.occurred_at)
        stmt = (
            select(
                bucket_col.label("bucket_start"),
                Event.asset_id.label("asset_id"),
                Event.unit.label("unit"),
                Event.category_id.label("category_id"),
                func.sum(Event.quantity).label("total"),
            )
            .where(
                Event.type == q.type,
                Event.quantity.is_not(None),
                Event.unit.is_not(None),
            )
            .group_by(bucket_col, Event.asset_id, Event.unit, Event.category_id)
            .order_by(bucket_col, Event.asset_id)
        )
        stmt = _scope(stmt, farm_id, q.date_from, q.date_to, q.asset_id)
        if q.unit is not None:
            stmt = stmt.where(Event.unit == q.unit)
        rows = (await self.db.execute(stmt)).mappings().all()
        data = [ProductionRow.model_validate(r) for r in rows]
        totals = _production_totals(data)
        return data, totals

    async def cost_per_unit(
        self, farm_id: int, q: CostPerUnitQuery
    ) -> tuple[list[CostPerUnitRow], list[CostPerUnitTotal]]:
        prod_stmt = (
            select(
                Event.asset_id.label("asset_id"),
                func.sum(Event.quantity).label("quantity"),
            )
            .where(
                Event.type == EventType.PRODUCTION,
                Event.unit == q.unit,
                Event.quantity.is_not(None),
            )
            .group_by(Event.asset_id)
        )
        prod_cte = _scope(prod_stmt, farm_id, q.date_from, q.date_to, q.asset_id).cte(
            "production_totals"
        )

        exp_stmt = (
            select(
                Event.asset_id.label("asset_id"),
                Event.currency.label("currency"),
                func.sum(Event.amount).label("expense_total"),
            )
            .where(
                Event.type == EventType.EXPENSE,
                Event.amount.is_not(None),
                Event.currency.is_not(None),
            )
            .group_by(Event.asset_id, Event.currency)
        )
        exp_cte = _scope(exp_stmt, farm_id, q.date_from, q.date_to, q.asset_id).cte(
            "expense_totals"
        )

        stmt = (
            select(
                Asset.id.label("asset_id"),
                Asset.name.label("asset_name"),
                exp_cte.c.currency,
                prod_cte.c.quantity,
                exp_cte.c.expense_total,
                (exp_cte.c.expense_total / prod_cte.c.quantity).label("cost_per_unit"),
            )
            .join(prod_cte, prod_cte.c.asset_id == Asset.id)
            .join(exp_cte, exp_cte.c.asset_id == Asset.id)
            .where(Asset.farm_id == farm_id, prod_cte.c.quantity > 0)
            .order_by(Asset.name, exp_cte.c.currency)
        )
        rows = (await self.db.execute(stmt)).mappings().all()
        data = [CostPerUnitRow.model_validate(r) for r in rows]
        totals = _cost_per_unit_totals(data)
        return data, totals

    async def timeline(
        self,
        farm_id: int,
        individual_id: int,
        q: TimelineQuery,
        page: PageParams,
    ) -> tuple[list[Event], int]:
        owner = await self.db.execute(
            select(Individual.id).where(
                Individual.id == individual_id,
                Individual.farm_id == farm_id,
            )
        )
        if owner.scalar_one_or_none() is None:
            raise NotFoundError("Individual not found")

        stmt = select(Event).where(
            Event.farm_id == farm_id,
            Event.individual_id == individual_id,
        )
        stmt = apply_date_range(stmt, Event.occurred_at, q.date_from, q.date_to)
        if q.type is not None:
            stmt = stmt.where(Event.type == q.type)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Event.occurred_at.desc()).offset(page.offset).limit(page.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total
