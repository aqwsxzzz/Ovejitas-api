"""Route for the production-productivity report — produced versus expected
output per (asset, product)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.report.deps import ReportSvc
from ovejitas.features.report.schemas_production import (
    ProductionProductivityQuery,
    ProductionProductivityReport,
)

router = APIRouter()


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
