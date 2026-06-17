from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from ovejitas.core.deps import DBSession
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.asset.schemas import (
    AssetCreate,
    AssetFilters,
    AssetKindCount,
    AssetRead,
    AssetSummary,
    AssetUpdate,
)
from ovejitas.features.asset.service import AssetService
from ovejitas.features.farm_member.deps import FarmMembership


def get_asset_service(db: DBSession) -> AssetService:
    return AssetService(db)


AssetSvc = Annotated[AssetService, Depends(get_asset_service)]

router = APIRouter(prefix="/farms/{farm_id}/assets", tags=["assets"])


@router.get("", response_model=Page[AssetRead], summary="List assets in a farm")
async def list_assets(
    farm_id: int,
    svc: AssetSvc,
    _membership: FarmMembership,
    page: Annotated[PageParams, Depends()],
    filters: Annotated[AssetFilters, Depends()],
    q: Annotated[str | None, Query(description="Search across name, description, location")] = None,
    sort: Annotated[str | None, Query(description="e.g. -created_at,name")] = None,
) -> Page[AssetRead]:
    rows, total = await svc.list_assets(
        farm_id=farm_id, filters=filters, search=q, sort=sort, page=page
    )
    return Page.build([AssetRead.model_validate(r) for r in rows], total, page)


@router.post(
    "",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an asset in a farm",
)
async def create_asset(
    farm_id: int,
    data: AssetCreate,
    svc: AssetSvc,
    _membership: FarmMembership,
) -> AssetRead:
    return AssetRead.model_validate(await svc.create(farm_id, data))


@router.get(
    "/summary",
    response_model=AssetSummary,
    summary="Count assets per kind in a farm",
)
async def asset_summary(
    farm_id: int,
    svc: AssetSvc,
    _membership: FarmMembership,
) -> AssetSummary:
    counts = await svc.count_by_kind(farm_id)
    return AssetSummary(data=[AssetKindCount(kind=kind, count=count) for kind, count in counts])


@router.get("/{asset_id}", response_model=AssetRead, summary="Get one asset")
async def get_asset(
    farm_id: int,
    asset_id: int,
    svc: AssetSvc,
    _membership: FarmMembership,
) -> AssetRead:
    return AssetRead.model_validate(await svc.get(farm_id, asset_id))


@router.patch("/{asset_id}", response_model=AssetRead, summary="Update an asset")
async def update_asset(
    farm_id: int,
    asset_id: int,
    data: AssetUpdate,
    svc: AssetSvc,
    _membership: FarmMembership,
) -> AssetRead:
    return AssetRead.model_validate(await svc.update(farm_id, asset_id, data))


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an asset",
)
async def delete_asset(
    farm_id: int,
    asset_id: int,
    svc: AssetSvc,
    _membership: FarmMembership,
) -> None:
    await svc.delete(farm_id, asset_id)
