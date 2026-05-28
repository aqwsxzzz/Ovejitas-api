from fastapi import APIRouter, status

from ovejitas.core.deps import DBSession
from ovejitas.features.asset.deps import AssetDep
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.flock.actions import (
    create_flock_acquisition,
    create_flock_mortality,
    create_flock_sale,
)
from ovejitas.features.flock.schemas import (
    FlockAcquisitionCreate,
    FlockActionRead,
    FlockMortalityCreate,
    FlockSaleCreate,
)

router = APIRouter(
    prefix="/farms/{farm_id}/assets/{asset_id}/flock",
    tags=["flock"],
)


@router.post(
    "/acquisitions",
    response_model=FlockActionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a flock acquisition",
    description=(
        "Increments the flock headcount by `quantity` head via an INVENTORY "
        "event; when `amount` is given, also books a paired EXPENSE in the "
        "farm's default currency. The asset must be `animal` + `aggregated`."
    ),
)
async def create_acquisition(
    asset: AssetDep,
    data: FlockAcquisitionCreate,
    db: DBSession,
    membership: FarmMembership,
) -> FlockActionRead:
    return await create_flock_acquisition(db, asset=asset, user_id=membership.user_id, data=data)


@router.post(
    "/sales",
    response_model=FlockActionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a flock sale",
    description=(
        "Decrements the flock headcount by `quantity` head and books a paired "
        "INCOME event for `amount`. Rejected with 409 if it would drive the "
        "headcount below zero."
    ),
)
async def create_sale(
    asset: AssetDep,
    data: FlockSaleCreate,
    db: DBSession,
    membership: FarmMembership,
) -> FlockActionRead:
    return await create_flock_sale(db, asset=asset, user_id=membership.user_id, data=data)


@router.post(
    "/mortalities",
    response_model=FlockActionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a flock mortality",
    description=(
        "Decrements the flock headcount by `quantity` head and emits a paired "
        "MORTALITY event. Rejected with 409 if it would drive the headcount "
        "below zero."
    ),
)
async def create_mortality(
    asset: AssetDep,
    data: FlockMortalityCreate,
    db: DBSession,
    membership: FarmMembership,
) -> FlockActionRead:
    return await create_flock_mortality(db, asset=asset, user_id=membership.user_id, data=data)
