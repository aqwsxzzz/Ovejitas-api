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
    AggregateQuery,
    AggregateReport,
    CoopProductivityQuery,
    CoopProductivityReport,
    CostPerUnitQuery,
    CostPerUnitReport,
    InventorySummaryQuery,
    InventorySummaryReport,
    MaterialConsumptionAggregateQuery,
    MaterialConsumptionAggregateReport,
    ProductionProductivityQuery,
    ProductionProductivityReport,
    ProfitabilityQuery,
    ProfitabilityReport,
    SalesValueQuery,
    SalesValueReport,
    TimelineQuery,
    UpcomingBirthsQuery,
    UpcomingBirthsReport,
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
    "/aggregate",
    response_model=AggregateReport,
    summary="Generic time-bucketed aggregate over events of one type",
    description=(
        "Dispatches on `type` and returns uniform "
        "`{bucket, group, group_label, measure, value, asset_id}` rows.\n\n"
        "- production / observation: SUM(quantity) grouped by unit\n"
        "- mortality / acquisition: SUM(quantity) as headcount, no grouping\n"
        "- inventory: net flow within window (increments minus decrements). "
        "  Pass `adjustment=reset|increment|decrement` to isolate one kind.\n"
        "- expense / income: SUM(amount) grouped by currency\n"
        "- reproductive: COUNT(*) of events\n\n"
        "Filters `unit`, `adjustment`, `currency` are ignored for types where "
        "they do not apply.\n\n"
        "**`group_by=asset`** breaks rows down per asset. Each row then carries a stable "
        "`group` key (the asset id as a string), a `group_label` (the asset name), and an "
        "`asset_id`. When `group_by` is omitted, rows are unchanged: `group_label` and "
        "`asset_id` stay `null`.\n\n"
        "Compatibility matrix — `type` vs `group_by`:\n\n"
        "| type | group_by=asset |\n"
        "| --- | --- |\n"
        "| mortality | supported |\n"
        "| acquisition | supported |\n"
        "| production | supported (quantity summed per asset across units) |\n"
        "| observation / inventory / expense / income / reproductive | "
        "rejected with 422 |\n"
    ),
)
async def aggregate_report(
    membership: FarmMembership,
    svc: ReportSvc,
    q: Annotated[AggregateQuery, Depends()],
) -> AggregateReport:
    rows, meta = await svc.aggregate(membership.farm_id, q)
    return AggregateReport(data=rows, meta=meta)


@router.get(
    "/material-consumption-aggregate",
    response_model=MaterialConsumptionAggregateReport,
    summary="Day/week material-consumption totals, bucketed and grouped",
    description=(
        "Time-bucketed SUM(quantity) over recorded material consumptions.\n\n"
        "- `bucket=day|week|month` — `date_trunc` window\n"
        "- `group_by=material|consumer|both` — each row carries a `group` key, a "
        "`group_label`, and the `unit` (quantities never sum across units)\n"
        "- optional filters: `material_asset_id`, `consumer_asset_id`, `reason`, "
        "`date_from`, `date_to`\n\n"
        "`totals` carries the per-(group, unit) `total_qty` across all buckets."
    ),
)
async def material_consumption_aggregate(
    membership: FarmMembership,
    svc: ReportSvc,
    q: Annotated[MaterialConsumptionAggregateQuery, Depends()],
) -> MaterialConsumptionAggregateReport:
    rows, totals = await svc.material_consumption_aggregate(membership.farm_id, q)
    return MaterialConsumptionAggregateReport(
        data=rows, totals=totals, bucket=q.bucket, group_by=q.group_by
    )


@router.get(
    "/cost-per-unit",
    response_model=CostPerUnitReport,
    summary="R3 — cost per produced unit, per producer asset",
    description=(
        "Requires `unit` (what counts as one produced unit). One row per "
        "producer asset (any asset with `production` events in that unit). "
        "`cost_per_unit = (direct expense events on the producer + the "
        "average-cost value of the feed it was fed) / its production quantity`. "
        "Feed is attributed via `material_consumption` with `reason=feeding` and "
        "`consumer_asset_id` = the producer; a material's average cost is its "
        "full purchase history (not bounded by `date_from`). `date_from`/"
        "`date_to` bound production and direct expenses. A producer that made "
        "nothing in the window still appears with `cost_per_unit` null; "
        "`has_unvalued_consumption` flags rows whose feed has no purchase "
        "history to value it."
    ),
)
async def cost_per_unit(
    membership: FarmMembership,
    svc: ReportSvc,
    q: Annotated[CostPerUnitQuery, Depends()],
) -> CostPerUnitReport:
    return await svc.cost_per_unit(membership.farm_id, q)


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


@router.get("/cost-per-unit/pdf", summary="R3 — PDF download")
async def cost_per_unit_pdf(
    membership: FarmMembership,
    current_user: CurrentUser,
    svc: ReportSvc,
    db: DBSession,
    q: Annotated[CostPerUnitQuery, Depends()],
) -> Response:
    report = await svc.cost_per_unit(membership.farm_id, q)
    pdf = render_pdf(
        "cost_per_unit.html",
        farm_name=await _farm_name(db, membership.farm_id),
        title="Costo por unidad",
        generated_by=current_user.name,
        date_from=q.date_from,
        date_to=q.date_to,
        context={"rows": report.data, "unit": report.unit},
    )
    return _pdf_response(pdf, "costo-por-unidad.pdf")


@router.get(
    "/sales-value",
    response_model=SalesValueReport,
    summary="Realized average sale price per unit, per asset",
    description=(
        "One row per asset sold via the sale action in the window. "
        "`value_per_unit = total sale income / total quantity sold` — the "
        "weighted-average price actually received (e.g. value per egg), derived "
        "from sale events, with no stored unit price. Only `material_sale` income "
        "and its paired inventory decrements are counted; manually entered income "
        "is excluded. When an asset was sold in more than one unit in the window, "
        "income can't be split across units, so `unit`/`quantity_sold`/"
        "`value_per_unit` are null and `ambiguous` is true. Assets with no sales "
        "in the window do not appear."
    ),
)
async def sales_value(
    membership: FarmMembership,
    svc: ReportSvc,
    q: Annotated[SalesValueQuery, Depends()],
) -> SalesValueReport:
    return await svc.sales_value(membership.farm_id, q)


@router.get(
    "/coop-productivity",
    response_model=CoopProductivityReport,
    summary="Eggs laid vs expected laying, per coop",
    description=(
        "One row per coop (animal asset) that either laid eggs in the window or "
        "has laying capacity configured. `produced` is eggs laid, normalized to "
        "single eggs (counts in `dozen` are x12). `expected = "
        "expected_eggs_per_head_per_day x headcount x days`, using the coop's "
        "current headcount for the whole window. `productivity_pct = produced / "
        "expected x 100`. A coop without `headcount` or "
        "`expected_eggs_per_head_per_day` set reports `missing_capacity: true` "
        "with null `expected`/`productivity_pct`. `date_from` and `date_to` are "
        "**required** (expected laying scales with the number of days)."
    ),
)
async def coop_productivity(
    membership: FarmMembership,
    svc: ReportSvc,
    q: Annotated[CoopProductivityQuery, Depends()],
) -> CoopProductivityReport:
    return await svc.coop_productivity(membership.farm_id, q)


@router.get(
    "/production-productivity",
    response_model=ProductionProductivityReport,
    summary="Produced vs expected output, per asset and product",
    description=(
        "One row per (asset, product) that either produced in the window or has "
        "an applicable production target. The product is a production category; "
        "`produced` is converted into the product's unit. `expected` comes from "
        "the target, scaled by its `basis` (per_head_continuous uses time-weighted "
        "animal-days). A pair with no applicable target reports "
        "`missing_capacity: true` with null `expected`/`productivity_pct`. "
        "`date_from` and `date_to` are **required**."
    ),
)
async def production_productivity(
    membership: FarmMembership,
    svc: ReportSvc,
    q: Annotated[ProductionProductivityQuery, Depends()],
) -> ProductionProductivityReport:
    return await svc.production_productivity(membership.farm_id, q)


@router.get(
    "/inventory-summary",
    response_model=InventorySummaryReport,
    summary="R5 — current on-hand inventory per asset",
    description=(
        "One row per (asset, unit) for any asset that carries INVENTORY events — "
        "material assets and aggregated animal flocks. On-hand is derived from "
        "those events: sum of increments minus decrements since the most recent "
        "reset. `date_to` gives the balance as of that moment (default: now); "
        "`date_from` does not apply to a running balance and is ignored."
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
    "/upcoming-births",
    response_model=UpcomingBirthsReport,
    summary="Individuals due to give birth within a window",
    description=(
        "One row per individual whose **latest** pregnancy check says pregnant "
        "with an `expected_due_at` inside `[date_from, date_to]`. A later "
        "not-pregnant check (after birth or loss) suppresses the alert. "
        "`date_from` and `date_to` are **required** — they define the alert "
        "window. `days_until_due` counts whole days from `date_from`."
    ),
)
async def upcoming_births(
    membership: FarmMembership,
    svc: ReportSvc,
    q: Annotated[UpcomingBirthsQuery, Depends()],
) -> UpcomingBirthsReport:
    rows = await svc.upcoming_births(membership.farm_id, q)
    return UpcomingBirthsReport(data=rows)


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
