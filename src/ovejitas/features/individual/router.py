from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from ovejitas.core.deps import DBSession
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.asset.deps import AssetDep
from ovejitas.features.farm.deps import farm_local
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.individual.birth import create_birth
from ovejitas.features.individual.schemas import (
    BirthCreate,
    BirthRead,
    IndividualCreate,
    IndividualFilters,
    IndividualRead,
    IndividualUpdate,
)
from ovejitas.features.individual.service import IndividualService


def get_individual_service(db: DBSession) -> IndividualService:
    return IndividualService(db)


IndividualSvc = Annotated[IndividualService, Depends(get_individual_service)]

router = APIRouter(
    prefix="/farms/{farm_id}/assets/{asset_id}/individuals",
    tags=["individuals"],
)


@router.get(
    "",
    response_model=Page[IndividualRead],
    summary="List individuals under an asset",
)
async def list_individuals(
    asset: AssetDep,
    svc: IndividualSvc,
    page: Annotated[PageParams, Depends()],
    filters: Annotated[IndividualFilters, Depends(farm_local(IndividualFilters))],
    q: Annotated[str | None, Query(description="Search across name, tag")] = None,
    sort: Annotated[str | None, Query(description="e.g. -created_at,name")] = None,
) -> Page[IndividualRead]:
    rows, total = await svc.list_individuals(
        asset=asset, filters=filters, search=q, sort=sort, page=page
    )
    return Page.build([IndividualRead.model_validate(r) for r in rows], total, page)


@router.post(
    "",
    response_model=IndividualRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an individual under an asset",
    description=(
        "Asset must be in `individual` mode. Parents (if any) must belong to the same farm. "
        "Atomically emits an ACQUISITION event; a `purchased` acquisition also books a "
        "paired EXPENSE event for `amount` in the farm's default currency."
    ),
)
async def create_individual(
    asset: AssetDep,
    data: IndividualCreate,
    svc: IndividualSvc,
    membership: FarmMembership,
) -> IndividualRead:
    return IndividualRead.model_validate(await svc.create(asset, membership.user_id, data))


@router.get(
    "/{individual_id}",
    response_model=IndividualRead,
    summary="Get one individual",
)
async def get_individual(
    asset: AssetDep,
    individual_id: int,
    svc: IndividualSvc,
) -> IndividualRead:
    return IndividualRead.model_validate(await svc.get(asset.id, individual_id))


@router.patch(
    "/{individual_id}",
    response_model=IndividualRead,
    summary="Update an individual",
    description=(
        "Transitioning `status` to `deceased` emits a MORTALITY event; `died_at` "
        "(defaults to now) and `cause` are recorded on it. Transitioning `status` "
        "to `sold` emits an INCOME event; `sale_amount` is required, `sold_at` "
        "(defaults to now) and `buyer` are optional. Transitioning away from either "
        "state reverses its event. Death/sale fields are rejected unless the "
        "individual is (or is becoming) deceased/sold respectively."
    ),
)
async def update_individual(
    asset: AssetDep,
    individual_id: int,
    data: IndividualUpdate,
    svc: IndividualSvc,
    membership: FarmMembership,
) -> IndividualRead:
    return IndividualRead.model_validate(
        await svc.update(asset, individual_id, membership.user_id, data)
    )


@router.post(
    "/{mother_id}/births",
    response_model=BirthRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a birth on a mother individual",
    description=(
        "Atomically emits a REPRODUCTIVE event on the mother and creates the "
        "offspring individuals, each with an ACQUISITION(`born`) event and its "
        "`birth_event_id` linked to that reproductive event. The mother must be "
        "`active` and under an `animal` asset."
    ),
)
async def create_birth_endpoint(
    asset: AssetDep,
    mother_id: int,
    data: BirthCreate,
    db: DBSession,
    membership: FarmMembership,
) -> BirthRead:
    reproductive, offspring = await create_birth(
        db, asset=asset, mother_id=mother_id, user_id=membership.user_id, data=data
    )
    return BirthRead(
        reproductive_event_id=reproductive.id,
        mother_id=mother_id,
        offspring=[IndividualRead.model_validate(c) for c in offspring],
    )


@router.delete(
    "/{individual_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an individual",
)
async def delete_individual(
    asset: AssetDep,
    individual_id: int,
    svc: IndividualSvc,
) -> None:
    await svc.delete(asset.id, individual_id)
