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
from ovejitas.features.event.types import EventType, InventoryAdjustment
from ovejitas.features.individual.models import Individual
from ovejitas.features.report.aggregate import aggregate as run_aggregate
from ovejitas.features.report.material_consumption import (
    material_consumption_aggregate as run_material_consumption_aggregate,
)
from ovejitas.features.report.production_cost import production_cost
from ovejitas.features.report.production_productivity import (
    production_productivity as run_production_productivity,
)
from ovejitas.features.report.profitability_full import (
    profitability_full as run_profitability_full,
)
from ovejitas.features.report.sales_value import sales_value as run_sales_value
from ovejitas.features.report.schemas import (
    AggregateMeta,
    AggregateQuery,
    AggregateRow,
    CostPerUnitQuery,
    CostPerUnitReport,
    InventorySummaryQuery,
    InventorySummaryRow,
    MaterialConsumptionAggregateQuery,
    MaterialConsumptionAggregateTotal,
    ProductionProductivityQuery,
    ProductionProductivityReport,
    SalesValueQuery,
    SalesValueReport,
    TimelineQuery,
    UpcomingBirthRow,
    UpcomingBirthsQuery,
)
from ovejitas.features.report.schemas_profitability import (
    ProfitabilityFullQuery,
    ProfitabilityFullReport,
    ProfitabilityQuery,
    ProfitabilityRow,
    ProfitabilityTotal,
)
from ovejitas.features.report.upcoming_births import upcoming_births as run_upcoming_births


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

    async def profitability_full(
        self, farm_id: int, q: ProfitabilityFullQuery
    ) -> ProfitabilityFullReport:
        return await run_profitability_full(self.db, farm_id, q)

    async def aggregate(
        self, farm_id: int, q: AggregateQuery
    ) -> tuple[list[AggregateRow], AggregateMeta]:
        return await run_aggregate(self.db, farm_id, q)

    async def material_consumption_aggregate(
        self, farm_id: int, q: MaterialConsumptionAggregateQuery
    ) -> tuple[list[AggregateRow], list[MaterialConsumptionAggregateTotal]]:
        return await run_material_consumption_aggregate(self.db, farm_id, q)

    async def cost_per_unit(self, farm_id: int, q: CostPerUnitQuery) -> CostPerUnitReport:
        return await production_cost(self.db, farm_id, q)

    async def sales_value(self, farm_id: int, q: SalesValueQuery) -> SalesValueReport:
        return await run_sales_value(self.db, farm_id, q)

    async def production_productivity(
        self, farm_id: int, q: ProductionProductivityQuery
    ) -> ProductionProductivityReport:
        return await run_production_productivity(self.db, farm_id, q)

    async def upcoming_births(self, farm_id: int, q: UpcomingBirthsQuery) -> list[UpcomingBirthRow]:
        return await run_upcoming_births(self.db, farm_id, q.date_from, q.date_to)

    async def inventory_summary(
        self, farm_id: int, q: InventorySummaryQuery
    ) -> list[InventorySummaryRow]:
        stmt = (
            select(
                Event.asset_id,
                Asset.name.label("asset_name"),
                Event.adjustment,
                Event.unit,
                Event.quantity,
                Event.occurred_at,
                Event.id,
            )
            .join(Asset, Asset.id == Event.asset_id)
            .where(
                Asset.farm_id == farm_id,
                Event.type == EventType.INVENTORY,
            )
            .order_by(Event.asset_id, Event.occurred_at.asc(), Event.id.asc())
        )
        # On-hand is a running balance — it must replay the full event history,
        # so date_from must NOT truncate it (dropping a prior RESET would make
        # the replay start mid-stream). date_to is an honest upper bound: the
        # balance "as of" that moment.
        stmt = apply_date_range(stmt, Event.occurred_at, None, q.date_to)
        if q.asset_id is not None:
            stmt = stmt.where(Event.asset_id == q.asset_id)
        rows = (await self.db.execute(stmt)).all()

        buckets: dict[tuple[int, Any], dict[str, Any]] = defaultdict(
            lambda: {"on_hand": Decimal(0), "asset_name": ""}
        )
        for asset_id, asset_name, adjustment, unit, quantity, _occurred_at, _id in rows:
            key = (asset_id, unit)
            bucket = buckets[key]
            bucket["asset_name"] = asset_name
            if adjustment is InventoryAdjustment.RESET:
                bucket["on_hand"] = Decimal(quantity)
            elif adjustment is InventoryAdjustment.INCREMENT:
                bucket["on_hand"] = Decimal(bucket["on_hand"]) + Decimal(quantity)
            elif adjustment is InventoryAdjustment.DECREMENT:
                bucket["on_hand"] = Decimal(bucket["on_hand"]) - Decimal(quantity)
        return [
            InventorySummaryRow(
                asset_id=asset_id,
                asset_name=vals["asset_name"],
                unit=unit,
                on_hand=Decimal(vals["on_hand"]),
            )
            for (asset_id, unit), vals in sorted(
                buckets.items(), key=lambda kv: (kv[1]["asset_name"], kv[0][1].value)
            )
        ]

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
