from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ConflictError, NotFoundError, ValidationError
from ovejitas.core.filters import apply_date_range
from ovejitas.core.pagination import PageParams
from ovejitas.core.search import apply_search
from ovejitas.core.sorting import apply_sort
from ovejitas.features.asset.deletion import blocking_reason, deletable_map
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
        self._reject_hand_authored_produce(data.kind)
        self._validate_kind_mode(data.kind, data.mode)
        self._validate_gestation_kind(data.kind, data.gestation_days)
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
        if "kind" in updates:
            self._reject_hand_authored_produce(updates["kind"])
        if "kind" in updates or "mode" in updates:
            self._validate_kind_mode(
                updates.get("kind", asset.kind), updates.get("mode", asset.mode)
            )
        if "kind" in updates or "gestation_days" in updates:
            self._validate_gestation_kind(
                updates.get("kind", asset.kind),
                updates.get("gestation_days", asset.gestation_days),
            )
        for key, value in updates.items():
            setattr(asset, key, value)
        await self.db.commit()
        await self.db.refresh(asset)
        return asset

    @staticmethod
    def _reject_hand_authored_produce(kind: AssetKind) -> None:
        """A produce pool belongs to a product and is created with it. Allowing one
        here is what let "Huevos" exist twice — as a category and as a look-alike
        asset — with nothing keeping the two in agreement."""
        if kind is AssetKind.PRODUCE:
            raise ValidationError(
                "Produce assets are created by their production category — "
                "create the category instead"
            )

    @staticmethod
    def _validate_kind_mode(kind: AssetKind, mode: AssetMode | None) -> None:
        """Only animals carry a tracking mode (they back the individual feature);
        every other kind leaves it null."""
        if kind is AssetKind.ANIMAL and mode is None:
            raise ValidationError("Animal assets require a tracking mode")

    @staticmethod
    def _validate_gestation_kind(kind: AssetKind, gestation_days: int | None) -> None:
        """Only animals gestate — a crop, a barn or a sack of feed does not."""
        if gestation_days is not None and kind is not AssetKind.ANIMAL:
            raise ValidationError("Only animal assets carry a gestation length")

    async def _validate_produce_link(
        self, farm_id: int, source_kind: AssetKind, produce_asset_id: int
    ) -> None:
        """A produce link is only meaningful on an asset that produces, and must
        point at a produce asset in the same farm."""
        if source_kind not in (AssetKind.ANIMAL, AssetKind.CROP):
            raise ValidationError("Only animal or crop assets can link a produce asset")
        target = await self.get(farm_id, produce_asset_id)
        if target.kind is not AssetKind.PRODUCE:
            raise ValidationError("produce_asset_id must reference a produce asset")

    async def delete(self, farm_id: int, asset_id: int) -> None:
        """Erase an asset, refusing once anything records it.

        The refusal is named before the delete is attempted so the farmer is told
        *which* record to go look at. The IntegrityError catch behind it is the
        backstop for any RESTRICT the guard does not yet know about — a 409 with
        a vague message still beats a 500 with an empty body.
        """
        asset = await self.get(farm_id, asset_id)
        reason = await blocking_reason(self.db, asset_id)
        if reason is not None:
            raise ConflictError(reason)
        try:
            await self.db.delete(asset)
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ConflictError(
                "Asset is referenced by another record and cannot be deleted"
            ) from exc

    async def is_deletable(self, asset_id: int) -> bool:
        """Whether DELETE on this asset would succeed — same check the guard runs."""
        return (await blocking_reason(self.db, asset_id)) is None

    async def deletable_flags(self, assets: Sequence[Asset]) -> dict[int, bool]:
        """The same answer for a whole page, in one query rather than one per row."""
        return await deletable_map(self.db, [asset.id for asset in assets])

    async def count_by_kind(self, farm_id: int) -> list[tuple[AssetKind, int]]:
        """One (kind, count) pair per kind present in the farm.

        Archived assets are left out: this feeds the "what do I have" summary,
        and a flock the farmer already sold is not something they still have.
        """
        stmt = (
            select(Asset.kind, func.count())
            .where(Asset.farm_id == farm_id, Asset.archived_at.is_(None))
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
        if filters.archived:
            stmt = stmt.where(Asset.archived_at.is_not(None))
        else:
            stmt = stmt.where(Asset.archived_at.is_(None))
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
