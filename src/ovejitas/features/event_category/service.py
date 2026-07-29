from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ConflictError, NotFoundError
from ovejitas.core.filters import apply_date_range
from ovejitas.core.pagination import PageParams
from ovejitas.core.search import apply_search
from ovejitas.core.sorting import apply_sort
from ovejitas.features.asset.provisioning import (
    build_produce_pool,
    rename_produce_pool,
    retire_produce_pool,
)
from ovejitas.features.event.types import EventType
from ovejitas.features.event_category.models import EventCategory
from ovejitas.features.event_category.schemas import (
    EventCategoryCreate,
    EventCategoryFilters,
    EventCategoryUpdate,
)

SEARCH_COLUMNS = [EventCategory.name]
SORT_ALLOWED = {
    "name": EventCategory.name,
    "type": EventCategory.type,
    "created_at": EventCategory.created_at,
    "updated_at": EventCategory.updated_at,
}


class EventCategoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, farm_id: int, data: EventCategoryCreate) -> EventCategory:
        category = EventCategory(farm_id=farm_id, **data.model_dump())
        if data.type is EventType.PRODUCTION:
            # A product owns the pool holding its stock; the farmer never creates
            # one by hand. Flushed first so the category can carry its id.
            pool = build_produce_pool(self.db, farm_id=farm_id, name=data.name)
            await self.db.flush()
            category.produce_asset_id = pool.id
        self.db.add(category)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ConflictError("Category with this type and name already exists") from exc
        await self.db.refresh(category)
        return category

    async def get(self, farm_id: int, category_id: int) -> EventCategory:
        stmt = select(EventCategory).where(
            EventCategory.id == category_id, EventCategory.farm_id == farm_id
        )
        category = (await self.db.execute(stmt)).scalar_one_or_none()
        if category is None:
            raise NotFoundError("Event category not found")
        return category

    async def update(
        self, farm_id: int, category_id: int, data: EventCategoryUpdate
    ) -> EventCategory:
        category = await self.get(farm_id, category_id)
        patch = data.model_dump(exclude_unset=True)
        for key, value in patch.items():
            setattr(category, key, value)
        new_name = patch.get("name")
        if new_name is not None and category.produce_asset_id is not None:
            # The pool wears the product's name on the stock and sale screens.
            # Renamed in the same transaction, or the two drift apart silently.
            await rename_produce_pool(self.db, category.produce_asset_id, new_name)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ConflictError("Category with this type and name already exists") from exc
        await self.db.refresh(category)
        return category

    async def delete(self, farm_id: int, category_id: int) -> None:
        category = await self.get(farm_id, category_id)
        pool_id = category.produce_asset_id
        await self.db.delete(category)
        if pool_id is not None:
            # Ordered: the referencing row goes first, or the RESTRICT on
            # produce_asset_id blocks the pool's delete.
            await self.db.flush()
            await retire_produce_pool(self.db, pool_id)
        await self.db.commit()

    async def list_categories(
        self,
        *,
        farm_id: int,
        filters: EventCategoryFilters,
        search: str | None,
        sort: str | None,
        page: PageParams,
    ) -> tuple[list[EventCategory], int]:
        stmt = select(EventCategory).where(EventCategory.farm_id == farm_id)
        if filters.type is not None:
            stmt = stmt.where(EventCategory.type == filters.type)
        if filters.archived is True:
            stmt = stmt.where(EventCategory.archived_at.is_not(None))
        elif filters.archived is False:
            stmt = stmt.where(EventCategory.archived_at.is_(None))
        stmt = apply_date_range(stmt, EventCategory.created_at, filters.date_from, filters.date_to)
        stmt = apply_search(stmt, search, SEARCH_COLUMNS)
        stmt = apply_sort(stmt, sort, SORT_ALLOWED)
        if sort is None:
            stmt = stmt.order_by(EventCategory.name.asc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.offset(page.offset).limit(page.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total
