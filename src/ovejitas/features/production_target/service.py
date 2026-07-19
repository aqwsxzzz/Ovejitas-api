from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ConflictError, NotFoundError, ValidationError
from ovejitas.core.pagination import PageParams
from ovejitas.core.sorting import apply_sort
from ovejitas.features.asset.models import Asset, AssetKind
from ovejitas.features.event.types import EventType
from ovejitas.features.event_category.models import EventCategory
from ovejitas.features.production_target.models import AssetProductionTarget
from ovejitas.features.production_target.schemas import (
    AssetProductionTargetCreate,
    AssetProductionTargetFilters,
    AssetProductionTargetUpdate,
)
from ovejitas.features.production_target.types import ProductionBasis

SORT_ALLOWED = {
    "effective_from": AssetProductionTarget.effective_from,
    "created_at": AssetProductionTarget.created_at,
    "updated_at": AssetProductionTarget.updated_at,
}


class ProductionTargetService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _validate_refs(
        self, farm_id: int, asset_id: int, category_id: int, basis: ProductionBasis
    ) -> None:
        asset = await self.db.get(Asset, asset_id)
        if asset is None or asset.farm_id != farm_id:
            raise NotFoundError("Asset not found in this farm")
        if basis is ProductionBasis.PER_HEAD_CONTINUOUS and asset.kind is not AssetKind.ANIMAL:
            raise ValidationError("per_head_continuous targets require an animal asset")
        category = await self.db.get(EventCategory, category_id)
        if category is None or category.farm_id != farm_id:
            raise NotFoundError("Category not found in this farm")
        if category.type is not EventType.PRODUCTION:
            raise ValidationError("Target category must be a production category")

    async def create(
        self, farm_id: int, data: AssetProductionTargetCreate
    ) -> AssetProductionTarget:
        await self._validate_refs(farm_id, data.asset_id, data.category_id, data.basis)
        target = AssetProductionTarget(farm_id=farm_id, **data.model_dump())
        self.db.add(target)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ConflictError(
                "A target for this asset, product and start date already exists"
            ) from exc
        await self.db.refresh(target)
        return target

    async def get(self, farm_id: int, target_id: int) -> AssetProductionTarget:
        stmt = select(AssetProductionTarget).where(
            AssetProductionTarget.id == target_id,
            AssetProductionTarget.farm_id == farm_id,
        )
        target = (await self.db.execute(stmt)).scalar_one_or_none()
        if target is None:
            raise NotFoundError("Production target not found")
        return target

    async def update(
        self, farm_id: int, target_id: int, data: AssetProductionTargetUpdate
    ) -> AssetProductionTarget:
        target = await self.get(farm_id, target_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(target, key, value)
        await self.db.commit()
        await self.db.refresh(target)
        return target

    async def delete(self, farm_id: int, target_id: int) -> None:
        target = await self.get(farm_id, target_id)
        await self.db.delete(target)
        await self.db.commit()

    async def list_targets(
        self,
        *,
        farm_id: int,
        filters: AssetProductionTargetFilters,
        sort: str | None,
        page: PageParams,
    ) -> tuple[list[AssetProductionTarget], int]:
        stmt = select(AssetProductionTarget).where(AssetProductionTarget.farm_id == farm_id)
        if filters.asset_id is not None:
            stmt = stmt.where(AssetProductionTarget.asset_id == filters.asset_id)
        if filters.category_id is not None:
            stmt = stmt.where(AssetProductionTarget.category_id == filters.category_id)
        if filters.basis is not None:
            stmt = stmt.where(AssetProductionTarget.basis == filters.basis)
        if filters.archived is True:
            stmt = stmt.where(AssetProductionTarget.archived_at.is_not(None))
        elif filters.archived is False:
            stmt = stmt.where(AssetProductionTarget.archived_at.is_(None))
        stmt = apply_sort(stmt, sort, SORT_ALLOWED)
        if sort is None:
            stmt = stmt.order_by(AssetProductionTarget.effective_from.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.offset(page.offset).limit(page.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total
