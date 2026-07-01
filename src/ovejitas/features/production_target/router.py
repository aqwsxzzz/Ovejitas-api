from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from ovejitas.core.deps import DBSession
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.production_target.schemas import (
    AssetProductionTargetCreate,
    AssetProductionTargetFilters,
    AssetProductionTargetRead,
    AssetProductionTargetUpdate,
)
from ovejitas.features.production_target.service import ProductionTargetService


def get_production_target_service(db: DBSession) -> ProductionTargetService:
    return ProductionTargetService(db)


ProductionTargetSvc = Annotated[ProductionTargetService, Depends(get_production_target_service)]

router = APIRouter(prefix="/farms/{farm_id}/production-targets", tags=["production-targets"])


@router.get(
    "",
    response_model=Page[AssetProductionTargetRead],
    summary="List production targets in a farm",
)
async def list_production_targets(
    farm_id: int,
    svc: ProductionTargetSvc,
    _membership: FarmMembership,
    page: Annotated[PageParams, Depends()],
    filters: Annotated[AssetProductionTargetFilters, Depends()],
    sort: Annotated[str | None, Query(description="e.g. -effective_from,created_at")] = None,
) -> Page[AssetProductionTargetRead]:
    rows, total = await svc.list_targets(farm_id=farm_id, filters=filters, sort=sort, page=page)
    return Page.build([AssetProductionTargetRead.model_validate(r) for r in rows], total, page)


@router.post(
    "",
    response_model=AssetProductionTargetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a production target",
    description="`basis`, `period`, `asset_id`, `category_id` are set once; a changed "
    "rate is a new effective-dated target, not an edit.",
)
async def create_production_target(
    farm_id: int,
    data: AssetProductionTargetCreate,
    svc: ProductionTargetSvc,
    _membership: FarmMembership,
) -> AssetProductionTargetRead:
    return AssetProductionTargetRead.model_validate(await svc.create(farm_id, data))


@router.get(
    "/{target_id}",
    response_model=AssetProductionTargetRead,
    summary="Get one production target",
)
async def get_production_target(
    farm_id: int,
    target_id: int,
    svc: ProductionTargetSvc,
    _membership: FarmMembership,
) -> AssetProductionTargetRead:
    return AssetProductionTargetRead.model_validate(await svc.get(farm_id, target_id))


@router.patch(
    "/{target_id}",
    response_model=AssetProductionTargetRead,
    summary="Update a production target",
    description="Adjust `expected_rate`, close `effective_to`, or set `archived_at`.",
)
async def update_production_target(
    farm_id: int,
    target_id: int,
    data: AssetProductionTargetUpdate,
    svc: ProductionTargetSvc,
    _membership: FarmMembership,
) -> AssetProductionTargetRead:
    return AssetProductionTargetRead.model_validate(await svc.update(farm_id, target_id, data))


@router.delete(
    "/{target_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a production target",
)
async def delete_production_target(
    farm_id: int,
    target_id: int,
    svc: ProductionTargetSvc,
    _membership: FarmMembership,
) -> None:
    await svc.delete(farm_id, target_id)
