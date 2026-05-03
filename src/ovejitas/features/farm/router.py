from typing import Annotated

from fastapi import APIRouter, Depends

from ovejitas.core.deps import DBSession
from ovejitas.features.farm.schemas import FarmRead, FarmUpdate
from ovejitas.features.farm.service import FarmService
from ovejitas.features.farm_member.deps import FarmMembership


def get_farm_service(db: DBSession) -> FarmService:
    return FarmService(db)


FarmSvc = Annotated[FarmService, Depends(get_farm_service)]

router = APIRouter(prefix="/farms", tags=["farms"])


@router.get("/{farm_id}", response_model=FarmRead, summary="Get a farm")
async def get_farm(
    farm_id: int,
    svc: FarmSvc,
    _membership: FarmMembership,
) -> FarmRead:
    return FarmRead.model_validate(await svc.get(farm_id))


@router.patch("/{farm_id}", response_model=FarmRead, summary="Update a farm")
async def update_farm(
    farm_id: int,
    data: FarmUpdate,
    svc: FarmSvc,
    _membership: FarmMembership,
) -> FarmRead:
    return FarmRead.model_validate(await svc.update(farm_id, data))
