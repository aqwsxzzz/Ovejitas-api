from fastapi import APIRouter, status

from ovejitas.core.deps import DBSession
from ovejitas.features.asset.deps import AssetDep
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.material_sale.actions import create_material_sale
from ovejitas.features.material_sale.schemas import MaterialSaleCreate, MaterialSaleRead

router = APIRouter(
    prefix="/farms/{farm_id}/assets/{asset_id}/sales",
    tags=["material-sales"],
)


@router.post(
    "",
    response_model=MaterialSaleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a material sale",
    description=(
        "Sells stock from a `material` asset: decrements the asset's inventory "
        "by `quantity` and books a paired INCOME event for `amount` in the "
        "farm's default currency. `unit` must match a unit the asset already "
        "holds stock in. Rejected with 409 if it would drive stock below zero."
    ),
)
async def create_sale(
    asset: AssetDep,
    data: MaterialSaleCreate,
    db: DBSession,
    membership: FarmMembership,
) -> MaterialSaleRead:
    return await create_material_sale(db, asset=asset, user_id=membership.user_id, data=data)
