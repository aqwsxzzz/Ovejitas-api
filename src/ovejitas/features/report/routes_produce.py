"""Route for the produce-outcome report — per-producer contribution to a pool
and what became of it."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ovejitas.features.farm.deps import farm_local
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.report.deps import ReportSvc
from ovejitas.features.report.schemas_produce import ProduceOutcomeQuery, ProduceOutcomeReport

router = APIRouter()


@router.get(
    "/produce-outcome",
    response_model=ProduceOutcomeReport,
    summary="Per-producer contribution to a produce pool, and what became of it",
    description=(
        "One row per (producer, produce asset). `produced` is what that producer "
        "harvested into the pool; `sold` and `lost` are its derived share of what "
        "later left the pool, and `income_total` the money that share earned.\n\n"
        "Shares are **derived, never stored**: pooled produce is fungible, so no "
        "per-producer income is ever observed. Each outflow consumes the pool's "
        "daily baskets oldest-first and is split within each basket in proportion "
        "to what each producer put in it, priced at that outflow's own unit price. "
        "Correcting a harvest changes this report the next time it is asked — "
        "nothing needs re-booking.\n\n"
        "`produced` is bounded by when the harvest happened; `sold`/`lost`/"
        "`income_total` by when the stock left. FIFO crosses window edges, so "
        "within a narrow window these are **not** expected to reconcile.\n\n"
        "`lost` is stock drawn at zero revenue (waste, spoilage) — produced but "
        "never earned from. Currencies are never summed: a producer whose output "
        "sold in more than one currency gets a null `currency` and "
        "`has_other_currency: true`. `unattributed_quantity` reports stock that "
        "left a pool with no lot behind it (a manual inventory increment, or "
        "stock carried across a reset)."
    ),
)
async def produce_outcome(
    membership: FarmMembership,
    svc: ReportSvc,
    q: Annotated[ProduceOutcomeQuery, Depends(farm_local(ProduceOutcomeQuery))],
) -> ProduceOutcomeReport:
    return await svc.produce_outcome(membership.farm_id, q)
