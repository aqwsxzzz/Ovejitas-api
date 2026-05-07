from typing import Annotated

from fastapi import Depends
from sqlalchemy import select

from ovejitas.core.deps import DBSession
from ovejitas.core.errors import NotFoundError
from ovejitas.features.asset.models import Asset
from ovejitas.features.farm_member.deps import FarmMembership


async def asset_by_id(
    farm_id: int,
    asset_id: int,
    _membership: FarmMembership,
    db: DBSession,
) -> Asset:
    stmt = select(Asset).where(Asset.id == asset_id, Asset.farm_id == farm_id)
    asset = (await db.execute(stmt)).scalar_one_or_none()
    if asset is None:
        raise NotFoundError("Asset not found")
    return asset


AssetDep = Annotated[Asset, Depends(asset_by_id)]
