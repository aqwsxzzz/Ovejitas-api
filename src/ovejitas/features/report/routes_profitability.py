"""Routes for the money reports — profitability, profitability-full, cost per
produced unit, and realized sale value, plus their PDF renderings."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from ovejitas.core.deps import DBSession
from ovejitas.features.auth.deps import CurrentUser
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.report.deps import ReportSvc, farm_name, pdf_response
from ovejitas.features.report.pdf import render_pdf
from ovejitas.features.report.schemas_profitability import (
    CostPerUnitQuery,
    CostPerUnitReport,
    ProfitabilityFullQuery,
    ProfitabilityFullReport,
    ProfitabilityQuery,
    ProfitabilityReport,
    SalesValueQuery,
    SalesValueReport,
)

router = APIRouter()


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
    "/profitability-full",
    response_model=ProfitabilityFullReport,
    summary="Income minus total cost (direct expense + feed) per (asset, currency)",
    description=(
        "One row per (asset, currency), like R1 — currencies are never summed or "
        "converted. Extends R1 with the average-cost value of the feed the asset "
        "consumed: `net_incl_materials = income - (direct expense + feed)`. Feed "
        "is valued in the currency of the purchases backing it (a mixed-currency "
        "material splits its cost across currency rows in proportion to the "
        "quantity purchased in each) and uses the same basis as cost-per-unit "
        "(R3), so the two never disagree. `has_unvalued_consumption` is true only "
        "when feed has no purchase basis in ANY currency; such feed contributes no "
        "cost. An asset whose sole activity is unvalued feed appears once with a "
        "null `currency`. The existing `net` (income - direct expense) is retained "
        "unchanged. `date_from`/`date_to` bound income and direct expense; feed is "
        "valued over full purchase history."
    ),
)
async def profitability_full(
    membership: FarmMembership,
    svc: ReportSvc,
    q: Annotated[ProfitabilityFullQuery, Depends()],
) -> ProfitabilityFullReport:
    return await svc.profitability_full(membership.farm_id, q)


@router.get(
    "/cost-per-unit",
    response_model=CostPerUnitReport,
    summary="R3 — cost per produced unit, per (producer asset, currency)",
    description=(
        "Requires `unit` (what counts as one produced unit). One row per "
        "(producer, currency) — any asset with `production` events in that unit; "
        "direct expense and feed are never summed across currencies, so a producer "
        "with costs in two currencies yields two rows. "
        "`cost_per_unit = (direct expense events on the producer + the "
        "average-cost value of the feed it was fed) / its production quantity`, in "
        "that row's currency. Feed is attributed via `material_consumption` with "
        "`reason=feeding` and `consumer_asset_id` = the producer, valued in the "
        "currency of the backing purchases (a mixed-currency material splits across "
        "currency rows); a material's average cost is its full purchase history "
        "(not bounded by `date_from`). `date_from`/`date_to` bound production and "
        "direct expenses. A producer that made nothing in the window still appears "
        "with `cost_per_unit` null; a producer with no cost in any currency appears "
        "once with a null `currency`. `has_unvalued_consumption` flags rows whose "
        "feed has no purchase history in ANY currency to value it."
    ),
)
async def cost_per_unit(
    membership: FarmMembership,
    svc: ReportSvc,
    q: Annotated[CostPerUnitQuery, Depends()],
) -> CostPerUnitReport:
    return await svc.cost_per_unit(membership.farm_id, q)


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
        farm_name=await farm_name(db, membership.farm_id),
        title="Rentabilidad",
        generated_by=current_user.name,
        date_from=q.date_from,
        date_to=q.date_to,
        context={"rows": rows, "totals": totals},
    )
    return pdf_response(pdf, "rentabilidad.pdf")


@router.get("/profitability-full/pdf", summary="Profitability-full — PDF download")
async def profitability_full_pdf(
    membership: FarmMembership,
    current_user: CurrentUser,
    svc: ReportSvc,
    db: DBSession,
    q: Annotated[ProfitabilityFullQuery, Depends()],
) -> Response:
    report = await svc.profitability_full(membership.farm_id, q)
    pdf = render_pdf(
        "profitability_full.html",
        farm_name=await farm_name(db, membership.farm_id),
        title="Rentabilidad (con insumos)",
        generated_by=current_user.name,
        date_from=q.date_from,
        date_to=q.date_to,
        context={"rows": report.data, "totals": report.totals},
    )
    return pdf_response(pdf, "rentabilidad-completa.pdf")


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
        farm_name=await farm_name(db, membership.farm_id),
        title="Costo por unidad",
        generated_by=current_user.name,
        date_from=q.date_from,
        date_to=q.date_to,
        context={"rows": report.data, "unit": report.unit},
    )
    return pdf_response(pdf, "costo-por-unidad.pdf")
