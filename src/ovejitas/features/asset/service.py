from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError
from ovejitas.core.filters import apply_date_range
from ovejitas.core.pagination import PageParams
from ovejitas.core.search import apply_search
from ovejitas.core.sorting import apply_sort
from ovejitas.features.asset.models import Asset
from ovejitas.features.asset.schemas import AssetCreate, AssetFilters, AssetUpdate

SEARCH_COLUMNS = [Asset.name, Asset.description, Asset.location]
SORT_ALLOWED = {
    "name": Asset.name,
    "kind": Asset.kind,
    "created_at": Asset.created_at,
    "updated_at": Asset.updated_at,
}


class AssetService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, farm_id: int, data: AssetCreate) -> Asset:
        asset = Asset(farm_id=farm_id, **data.model_dump())
        self.db.add(asset)
        await self.db.commit()
        await self.db.refresh(asset)
        return asset

    async def get(self, farm_id: int, asset_id: int) -> Asset:
        stmt = select(Asset).where(Asset.id == asset_id, Asset.farm_id == farm_id)
        asset = (await self.db.execute(stmt)).scalar_one_or_none()
        if asset is None:
            raise NotFoundError("Asset not found")
        return asset

    async def update(self, farm_id: int, asset_id: int, data: AssetUpdate) -> Asset:
        asset = await self.get(farm_id, asset_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(asset, key, value)
        await self.db.commit()
        await self.db.refresh(asset)
        return asset

    async def delete(self, farm_id: int, asset_id: int) -> None:
        asset = await self.get(farm_id, asset_id)
        await self.db.delete(asset)
        await self.db.commit()

    async def list_assets(
        self,
        *,
        farm_id: int,
        filters: AssetFilters,
        search: str | None,
        sort: str | None,
        page: PageParams,
    ) -> tuple[list[Asset], int]:
        stmt = select(Asset).where(Asset.farm_id == farm_id)
        if filters.kind is not None:
            stmt = stmt.where(Asset.kind == filters.kind)
        if filters.mode is not None:
            stmt = stmt.where(Asset.mode == filters.mode)
        stmt = apply_date_range(stmt, Asset.created_at, filters.date_from, filters.date_to)
        stmt = apply_search(stmt, search, SEARCH_COLUMNS)
        stmt = apply_sort(stmt, sort, SORT_ALLOWED)
        if sort is None:
            stmt = stmt.order_by(Asset.created_at.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.offset(page.offset).limit(page.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total
