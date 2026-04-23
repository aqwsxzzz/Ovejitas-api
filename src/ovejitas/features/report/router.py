from typing import Annotated

from fastapi import APIRouter, Depends

from ovejitas.core.deps import DBSession
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.event.schemas import EventRead
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.report.schemas import (
    CostPerUnitQuery,
    CostPerUnitReport,
    ProductionQuery,
    ProductionReport,
    ProfitabilityQuery,
    ProfitabilityReport,
    TimelineQuery,
)
from ovejitas.features.report.service import ReportService


def get_report_service(db: DBSession) -> ReportService:
    return ReportService(db)


ReportSvc = Annotated[ReportService, Depends(get_report_service)]

router = APIRouter(prefix="/farms/{farm_id}/reports", tags=["reports"])


@router.get(
    "/profitability",
    response_model=ProfitabilityReport,
    summary="R1 — income minus expense per asset",
    description=(
        "One row per (asset, currency). Events with NULL amount/currency are excluded. "
        "Different currencies are never silently summed."
    ),
)
async def profitability(
    membership: FarmMembership,
    svc: ReportSvc,
    q: Annotated[ProfitabilityQuery, Depends()],
) -> ProfitabilityReport:
    rows = await svc.profitability(membership.farm_id, q)
    return ProfitabilityReport(data=rows)


@router.get(
    "/production",
    response_model=ProductionReport,
    summary="R2 — SUM(quantity) bucketed over time",
    description=(
        "Default type=production. Pass type=observation + unit=unit to get headcount deltas. "
        "Grouped by (bucket, asset_id, unit, category_id)."
    ),
)
async def production(
    membership: FarmMembership,
    svc: ReportSvc,
    q: Annotated[ProductionQuery, Depends()],
) -> ProductionReport:
    rows = await svc.production(membership.farm_id, q)
    return ProductionReport(data=rows, bucket=q.bucket, type=q.type)


@router.get(
    "/cost-per-unit",
    response_model=CostPerUnitReport,
    summary="R3 — expense total ÷ produced quantity, per asset",
    description=(
        "Requires `unit` (what counts as one produced unit). "
        "One row per (asset, currency). "
        "Assets without BOTH production (in the given unit) and expense events "
        "are omitted — a currency cannot be inferred without an expense row. "
        "The expense total is not unit-filtered: all of the asset's expenses "
        "are attributed to the queried production unit, so this number is only "
        "meaningful for single-output assets."
    ),
)
async def cost_per_unit(
    membership: FarmMembership,
    svc: ReportSvc,
    q: Annotated[CostPerUnitQuery, Depends()],
) -> CostPerUnitReport:
    rows = await svc.cost_per_unit(membership.farm_id, q)
    return CostPerUnitReport(data=rows, unit=q.unit)


@router.get(
    "/individuals/{individual_id}/timeline",
    response_model=Page[EventRead],
    summary="R4 — paginated event timeline for one individual",
)
async def timeline(
    membership: FarmMembership,
    individual_id: int,
    svc: ReportSvc,
    page: Annotated[PageParams, Depends()],
    q: Annotated[TimelineQuery, Depends()],
) -> Page[EventRead]:
    rows, total = await svc.timeline(
        farm_id=membership.farm_id,
        individual_id=individual_id,
        q=q,
        page=page,
    )
    return Page.build([EventRead.model_validate(r) for r in rows], total, page)
