from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select

from ovejitas.core.deps import DBSession
from ovejitas.core.errors import NotFoundError
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.auth.deps import CurrentUser
from ovejitas.features.event.schemas import EventRead
from ovejitas.features.farm.models import Farm
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.report.pdf import render_pdf
from ovejitas.features.report.schemas import (
    CostPerUnitQuery,
    CostPerUnitReport,
    InventorySummaryQuery,
    InventorySummaryReport,
    ProductionQuery,
    ProductionReport,
    ProfitabilityQuery,
    ProfitabilityReport,
    TimelineQuery,
)
from ovejitas.features.report.service import ReportService


async def _farm_name(db: DBSession, farm_id: int) -> str:
    name = (await db.execute(select(Farm.name).where(Farm.id == farm_id))).scalar_one_or_none()
    if name is None:
        raise NotFoundError("Farm not found")
    return name


def _pdf_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
    rows, totals = await svc.profitability(membership.farm_id, q)
    return ProfitabilityReport(data=rows, totals=totals)


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
    rows, totals = await svc.production(membership.farm_id, q)
    return ProductionReport(data=rows, totals=totals, bucket=q.bucket, type=q.type)


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
    rows, totals = await svc.cost_per_unit(membership.farm_id, q)
    return CostPerUnitReport(data=rows, totals=totals, unit=q.unit)


@router.get("/profitability/pdf", summary="R1 — PDF download")
async def profitability_pdf(
    membership: FarmMembership,
    current_user: CurrentUser,
    svc: ReportSvc,
    db: DBSession,
    q: Annotated[ProfitabilityQuery, Depends()],
) -> Response:
    rows, totals = await svc.profitability(membership.farm_id, q)
    pdf = render_pdf(
        "profitability.html",
        farm_name=await _farm_name(db, membership.farm_id),
        title="Rentabilidad",
        generated_by=current_user.name,
        date_from=q.date_from,
        date_to=q.date_to,
        context={"rows": rows, "totals": totals},
    )
    return _pdf_response(pdf, "rentabilidad.pdf")


@router.get("/production/pdf", summary="R2 — PDF download")
async def production_pdf(
    membership: FarmMembership,
    current_user: CurrentUser,
    svc: ReportSvc,
    db: DBSession,
    q: Annotated[ProductionQuery, Depends()],
) -> Response:
    rows, totals = await svc.production(membership.farm_id, q)
    pdf = render_pdf(
        "production.html",
        farm_name=await _farm_name(db, membership.farm_id),
        title="Producción",
        generated_by=current_user.name,
        date_from=q.date_from,
        date_to=q.date_to,
        context={"rows": rows, "totals": totals, "bucket": q.bucket, "type": q.type},
    )
    return _pdf_response(pdf, "produccion.pdf")


@router.get("/cost-per-unit/pdf", summary="R3 — PDF download")
async def cost_per_unit_pdf(
    membership: FarmMembership,
    current_user: CurrentUser,
    svc: ReportSvc,
    db: DBSession,
    q: Annotated[CostPerUnitQuery, Depends()],
) -> Response:
    rows, totals = await svc.cost_per_unit(membership.farm_id, q)
    pdf = render_pdf(
        "cost_per_unit.html",
        farm_name=await _farm_name(db, membership.farm_id),
        title="Costo por unidad",
        generated_by=current_user.name,
        date_from=q.date_from,
        date_to=q.date_to,
        context={"rows": rows, "totals": totals, "unit": q.unit},
    )
    return _pdf_response(pdf, "costo-por-unidad.pdf")


@router.get(
    "/inventory-summary",
    response_model=InventorySummaryReport,
    summary="R5 — current on-hand inventory across material assets",
    description=(
        "One row per (material asset, unit). On-hand is derived from INVENTORY "
        "events: sum of increments minus decrements since the most recent reset. "
        "Date filters bound the events considered, not the resulting balance."
    ),
)
async def inventory_summary(
    membership: FarmMembership,
    svc: ReportSvc,
    q: Annotated[InventorySummaryQuery, Depends()],
) -> InventorySummaryReport:
    rows = await svc.inventory_summary(membership.farm_id, q)
    return InventorySummaryReport(data=rows)


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
