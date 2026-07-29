from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from ovejitas.core.deps import DBSession
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.farm.deps import farm_local
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.material_consumption.schemas import (
    MaterialConsumptionCreate,
    MaterialConsumptionFilters,
    MaterialConsumptionRead,
    MaterialConsumptionUpdate,
)
from ovejitas.features.material_consumption.service import MaterialConsumptionService


def get_material_consumption_service(db: DBSession) -> MaterialConsumptionService:
    return MaterialConsumptionService(db)


MaterialConsumptionSvc = Annotated[
    MaterialConsumptionService, Depends(get_material_consumption_service)
]

router = APIRouter(
    prefix="/farms/{farm_id}/material-consumptions",
    tags=["material-consumptions"],
)


@router.get(
    "",
    response_model=Page[MaterialConsumptionRead],
    summary="List material consumptions in a farm",
)
async def list_material_consumptions(
    farm_id: int,
    svc: MaterialConsumptionSvc,
    _membership: FarmMembership,
    page: Annotated[PageParams, Depends()],
    filters: Annotated[MaterialConsumptionFilters, Depends(farm_local(MaterialConsumptionFilters))],
    q: Annotated[str | None, Query(description="Search notes")] = None,
    sort: Annotated[str | None, Query(description="e.g. -occurred_at,quantity")] = None,
) -> Page[MaterialConsumptionRead]:
    rows, total = await svc.list_consumptions(
        farm_id=farm_id, filters=filters, search=q, sort=sort, page=page
    )
    return Page.build([MaterialConsumptionRead.model_validate(r) for r in rows], total, page)


@router.post(
    "",
    response_model=MaterialConsumptionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a material consumption",
    description=(
        "Atomically records the consumption and decrements the material's stock "
        "via a paired INVENTORY event. `reason=feeding` requires `consumer_asset_id`; "
        "`waste`/`spoilage` must omit it. The consumed `unit` must match a unit the "
        "material already holds stock in. Rejects with 409 `insufficient_stock` if "
        "stock would go negative. Replaying an `idempotency_key` returns the original "
        "record with status 200."
    ),
)
async def create_material_consumption(
    farm_id: int,
    data: MaterialConsumptionCreate,
    svc: MaterialConsumptionSvc,
    membership: FarmMembership,
    response: Response,
) -> MaterialConsumptionRead:
    consumption, created = await svc.create(farm_id, membership.user_id, data)
    if not created:
        response.status_code = status.HTTP_200_OK
    return MaterialConsumptionRead.model_validate(consumption)


@router.get(
    "/{consumption_id}",
    response_model=MaterialConsumptionRead,
    summary="Get one material consumption",
)
async def get_material_consumption(
    farm_id: int,
    consumption_id: int,
    svc: MaterialConsumptionSvc,
    _membership: FarmMembership,
) -> MaterialConsumptionRead:
    return MaterialConsumptionRead.model_validate(await svc.get(farm_id, consumption_id))


@router.patch(
    "/{consumption_id}",
    response_model=MaterialConsumptionRead,
    summary="Update a material consumption",
    description=(
        "`material_asset_id` is immutable. Changing `quantity`/`unit`/`occurred_at` "
        "reconciles the paired inventory event and re-checks stock."
    ),
)
async def update_material_consumption(
    farm_id: int,
    consumption_id: int,
    data: MaterialConsumptionUpdate,
    svc: MaterialConsumptionSvc,
    _membership: FarmMembership,
) -> MaterialConsumptionRead:
    return MaterialConsumptionRead.model_validate(await svc.update(farm_id, consumption_id, data))


@router.delete(
    "/{consumption_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a material consumption",
    description="Hard-deletes the record and reverses its stock effect.",
)
async def delete_material_consumption(
    farm_id: int,
    consumption_id: int,
    svc: MaterialConsumptionSvc,
    _membership: FarmMembership,
) -> None:
    await svc.delete(farm_id, consumption_id)
