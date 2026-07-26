"""Routes for the per-individual reports — upcoming births and the event
timeline of one animal."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.event.schemas import EventRead
from ovejitas.features.farm.deps import farm_local
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.report.deps import ReportSvc
from ovejitas.features.report.schemas_individual import (
    TimelineQuery,
    UpcomingBirthsQuery,
    UpcomingBirthsReport,
)

router = APIRouter()


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
    q: Annotated[UpcomingBirthsQuery, Depends(farm_local(UpcomingBirthsQuery))],
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
    q: Annotated[TimelineQuery, Depends(farm_local(TimelineQuery))],
) -> Page[EventRead]:
    rows, total = await svc.timeline(
        farm_id=membership.farm_id,
        individual_id=individual_id,
        q=q,
        page=page,
    )
    return Page.build([EventRead.model_validate(r) for r in rows], total, page)
