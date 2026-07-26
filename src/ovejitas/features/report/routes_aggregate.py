"""Routes for the time-bucketed aggregate reports — the generic event
aggregate and the material-consumption aggregate."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ovejitas.features.farm.deps import farm_local
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.report.deps import ReportSvc
from ovejitas.features.report.schemas_aggregate import (
    AggregateQuery,
    AggregateReport,
    MaterialConsumptionAggregateQuery,
    MaterialConsumptionAggregateReport,
)

router = APIRouter()


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
    q: Annotated[AggregateQuery, Depends(farm_local(AggregateQuery))],
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
    q: Annotated[
        MaterialConsumptionAggregateQuery, Depends(farm_local(MaterialConsumptionAggregateQuery))
    ],
) -> MaterialConsumptionAggregateReport:
    rows, totals = await svc.material_consumption_aggregate(membership.farm_id, q)
    return MaterialConsumptionAggregateReport(
        data=rows, totals=totals, bucket=q.bucket, group_by=q.group_by
    )
