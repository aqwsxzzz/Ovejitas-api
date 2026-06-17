from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError, ValidationError
from ovejitas.core.filters import apply_date_range
from ovejitas.core.pagination import PageParams
from ovejitas.core.search import apply_search
from ovejitas.core.sorting import apply_sort
from ovejitas.features.asset.models import Asset, AssetKind, AssetMode
from ovejitas.features.asset.schemas import AssetCreate, AssetFilters, AssetUpdate
from ovejitas.features.event.balance import asset_has_events

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
        self._validate_kind_mode(data.kind, data.mode)
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
        updates = data.model_dump(exclude_unset=True)
        if updates.get("produce_asset_id") is not None:
            source_kind = updates.get("kind", asset.kind)
            await self._validate_produce_link(farm_id, source_kind, updates["produce_asset_id"])
        structural_changed = ("kind" in updates and updates["kind"] != asset.kind) or (
            "mode" in updates and updates["mode"] != asset.mode
        )
        if structural_changed and await asset_has_events(self.db, asset_id):
            raise ValidationError("Cannot change kind or mode of an asset that already has events")
        if "kind" in updates or "mode" in updates:
            self._validate_kind_mode(
                updates.get("kind", asset.kind), updates.get("mode", asset.mode)
            )
        for key, value in updates.items():
            setattr(asset, key, value)
        await self.db.commit()
        await self.db.refresh(asset)
        return asset

    @staticmethod
    def _validate_kind_mode(kind: AssetKind, mode: AssetMode | None) -> None:
        """Only animals carry a tracking mode (they back the individual feature);
        every other kind leaves it null."""
        if kind is AssetKind.ANIMAL and mode is None:
            raise ValidationError("Animal assets require a tracking mode")

    async def _validate_produce_link(
        self, farm_id: int, source_kind: AssetKind, produce_asset_id: int
    ) -> None:
        """A produce link is only meaningful on an asset that produces, and must
        point at a material asset in the same farm."""
        if source_kind not in (AssetKind.ANIMAL, AssetKind.CROP):
            raise ValidationError("Only animal or crop assets can link a produce asset")
        target = await self.get(farm_id, produce_asset_id)
        if target.kind is not AssetKind.MATERIAL:
            raise ValidationError("produce_asset_id must reference a material asset")

    async def delete(self, farm_id: int, asset_id: int) -> None:
        asset = await self.get(farm_id, asset_id)
        await self.db.delete(asset)
        await self.db.commit()

    async def count_by_kind(self, farm_id: int) -> list[tuple[AssetKind, int]]:
        """One (kind, count) pair per kind present in the farm."""
        stmt = (
            select(Asset.kind, func.count())
            .where(Asset.farm_id == farm_id)
            .group_by(Asset.kind)
            .order_by(Asset.kind)
        )
        rows = (await self.db.execute(stmt)).all()
        return [(kind, count) for kind, count in rows]

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
