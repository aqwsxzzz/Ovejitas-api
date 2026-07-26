"""Route for the inventory-summary report — current on-hand stock per asset."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ovejitas.features.farm.deps import farm_local
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.report.deps import ReportSvc
from ovejitas.features.report.schemas_inventory import (
    InventorySummaryQuery,
    InventorySummaryReport,
)

router = APIRouter()


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
    q: Annotated[InventorySummaryQuery, Depends(farm_local(InventorySummaryQuery))],
) -> InventorySummaryReport:
    rows = await svc.inventory_summary(membership.farm_id, q)
    return InventorySummaryReport(data=rows)
