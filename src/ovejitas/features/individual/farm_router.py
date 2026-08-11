"""The farm-scoped individual list. The per-asset routes live in ``router.py``."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ovejitas.core.deps import DBSession
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.farm.deps import farm_local
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.individual.farm_list import list_farm_individuals
from ovejitas.features.individual.schemas import FarmIndividualFilters, IndividualRead

router = APIRouter(prefix="/farms/{farm_id}/individuals", tags=["individuals"])


@router.get(
    "",
    response_model=Page[IndividualRead],
    summary="List every individual in a farm",
    description=(
        "Farm-wide counterpart to the per-asset list, for cases that span lots — "
        "picking a sire kept apart from the females, for one. Filter with "
        "`status=active` and `asset_id`; search across tag and name."
    ),
)
async def list_farm_individuals_endpoint(
    farm_id: int,
    db: DBSession,
    _membership: FarmMembership,
    page: Annotated[PageParams, Depends()],
    filters: Annotated[FarmIndividualFilters, Depends(farm_local(FarmIndividualFilters))],
    q: Annotated[str | None, Query(description="Search across name, tag")] = None,
    sort: Annotated[str | None, Query(description="e.g. -created_at,tag")] = None,
) -> Page[IndividualRead]:
    rows, total = await list_farm_individuals(
        db, farm_id=farm_id, filters=filters, search=q, sort=sort, page=page
    )
    return Page.build([IndividualRead.model_validate(r) for r in rows], total, page)
