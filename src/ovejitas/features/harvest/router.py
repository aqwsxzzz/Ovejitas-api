from fastapi import APIRouter, status

from ovejitas.core.deps import DBSession
from ovejitas.features.asset.deps import AssetDep
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.harvest.actions import create_harvest
from ovejitas.features.harvest.schemas import HarvestCreate, HarvestRead

router = APIRouter(
    prefix="/farms/{farm_id}/assets/{asset_id}/harvests",
    tags=["harvest"],
)


@router.post(
    "",
    response_model=HarvestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a harvest",
    description=(
        "Collects produce from an `animal` or `crop` asset: emits a PRODUCTION "
        "event on the source asset and an INVENTORY increment on the produce "
        "asset linked via the source's `produce_asset_id`. `quantity` and "
        "`unit` feed both events; `unit` must match the produce asset's "
        "existing stock unit. The source asset must have a produce asset linked."
    ),
)
async def create_harvest_endpoint(
    asset: AssetDep,
    data: HarvestCreate,
    db: DBSession,
    membership: FarmMembership,
) -> HarvestRead:
    return await create_harvest(db, asset=asset, user_id=membership.user_id, data=data)
