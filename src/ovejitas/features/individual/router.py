from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from ovejitas.core.deps import DBSession
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.asset.deps import AssetDep
from ovejitas.features.individual.schemas import (
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
    filters: Annotated[IndividualFilters, Depends()],
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
        "Asset must be in `individual` mode. Parents (if any) must belong to the same farm."
    ),
)
async def create_individual(
    asset: AssetDep,
    data: IndividualCreate,
    svc: IndividualSvc,
) -> IndividualRead:
    return IndividualRead.model_validate(await svc.create(asset, data))


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
)
async def update_individual(
    asset: AssetDep,
    individual_id: int,
    data: IndividualUpdate,
    svc: IndividualSvc,
) -> IndividualRead:
    return IndividualRead.model_validate(await svc.update(asset, individual_id, data))


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
