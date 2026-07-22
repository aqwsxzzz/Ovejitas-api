"""Report facade — one method per report, each delegating to the module that
owns that report's query. The service holds no report logic itself; it exists
so routers depend on a single injectable rather than a dozen functions."""

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.pagination import PageParams
from ovejitas.features.event.models import Event
from ovejitas.features.report.aggregate import aggregate as run_aggregate
from ovejitas.features.report.inventory_summary import (
    inventory_summary as run_inventory_summary,
)
from ovejitas.features.report.material_consumption import (
    material_consumption_aggregate as run_material_consumption_aggregate,
)
from ovejitas.features.report.produce_outcome import produce_outcome as run_produce_outcome
from ovejitas.features.report.production_cost import production_cost
from ovejitas.features.report.production_productivity import (
    production_productivity as run_production_productivity,
)
from ovejitas.features.report.profitability import profitability as run_profitability
from ovejitas.features.report.profitability_full import (
    profitability_full as run_profitability_full,
)
from ovejitas.features.report.sales_value import sales_value as run_sales_value
from ovejitas.features.report.schemas_aggregate import (
    AggregateMeta,
    AggregateQuery,
    AggregateRow,
    MaterialConsumptionAggregateQuery,
    MaterialConsumptionAggregateTotal,
)
from ovejitas.features.report.schemas_individual import (
    TimelineQuery,
    UpcomingBirthRow,
    UpcomingBirthsQuery,
)
from ovejitas.features.report.schemas_inventory import (
    InventorySummaryQuery,
    InventorySummaryRow,
)
from ovejitas.features.report.schemas_produce import ProduceOutcomeQuery, ProduceOutcomeReport
from ovejitas.features.report.schemas_production import (
    ProductionProductivityQuery,
    ProductionProductivityReport,
)
from ovejitas.features.report.schemas_profitability import (
    CostPerUnitQuery,
    CostPerUnitReport,
    ProfitabilityFullQuery,
    ProfitabilityFullReport,
    ProfitabilityQuery,
    ProfitabilityRow,
    ProfitabilityTotal,
    SalesValueQuery,
    SalesValueReport,
)
from ovejitas.features.report.timeline import timeline as run_timeline
from ovejitas.features.report.upcoming_births import upcoming_births as run_upcoming_births


class ReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def profitability(
        self, farm_id: int, q: ProfitabilityQuery
    ) -> tuple[list[ProfitabilityRow], list[ProfitabilityTotal]]:
        return await run_profitability(self.db, farm_id, q)

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

    async def produce_outcome(self, farm_id: int, q: ProduceOutcomeQuery) -> ProduceOutcomeReport:
        return await run_produce_outcome(self.db, farm_id, q)

    async def production_productivity(
        self, farm_id: int, q: ProductionProductivityQuery
    ) -> ProductionProductivityReport:
        return await run_production_productivity(self.db, farm_id, q)

    async def upcoming_births(self, farm_id: int, q: UpcomingBirthsQuery) -> list[UpcomingBirthRow]:
        return await run_upcoming_births(self.db, farm_id, q.date_from, q.date_to)

    async def inventory_summary(
        self, farm_id: int, q: InventorySummaryQuery
    ) -> list[InventorySummaryRow]:
        return await run_inventory_summary(self.db, farm_id, q)

    async def timeline(
        self,
        farm_id: int,
        individual_id: int,
        q: TimelineQuery,
        page: PageParams,
    ) -> tuple[list[Event], int]:
        return await run_timeline(self.db, farm_id, individual_id, q, page)
