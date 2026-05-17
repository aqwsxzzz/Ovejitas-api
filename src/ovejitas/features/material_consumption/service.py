from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ConflictError, NotFoundError
from ovejitas.core.filters import apply_date_range
from ovejitas.core.pagination import PageParams
from ovejitas.core.search import apply_search
from ovejitas.core.sorting import apply_sort
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.inventory import emit_decrement, reconcile_decrement, reverse_decrement
from ovejitas.features.event.models import Event
from ovejitas.features.material_consumption.guards import (
    assert_consumer_rules,
    validate_consumer,
    validate_material_asset,
    validate_unit_in_stock,
)
from ovejitas.features.material_consumption.models import MaterialConsumption
from ovejitas.features.material_consumption.schemas import (
    MaterialConsumptionCreate,
    MaterialConsumptionFilters,
    MaterialConsumptionUpdate,
)

SEARCH_COLUMNS = [MaterialConsumption.notes]
SORT_ALLOWED = {
    "occurred_at": MaterialConsumption.occurred_at,
    "quantity": MaterialConsumption.quantity,
    "created_at": MaterialConsumption.created_at,
    "updated_at": MaterialConsumption.updated_at,
}

_STOCK_FIELDS = {"quantity", "unit", "occurred_at"}


class MaterialConsumptionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, farm_id: int, user_id: int, data: MaterialConsumptionCreate
    ) -> tuple[MaterialConsumption, bool]:
        """Returns (record, created). ``created`` is False on idempotency-key replay."""
        if data.idempotency_key is not None:
            existing = await self._by_idempotency_key(farm_id, data.idempotency_key)
            if existing is not None:
                return existing, False
        material = await self._validate_create(farm_id, data)
        try:
            event = await emit_decrement(
                self.db,
                material=material,
                unit=data.unit,
                quantity=data.quantity,
                occurred_at=data.occurred_at,
                created_by=user_id,
            )
            consumption = MaterialConsumption(
                farm_id=farm_id,
                inventory_event_id=event.id,
                created_by=user_id,
                **data.model_dump(),
            )
            self.db.add(consumption)
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            replay = await self._by_idempotency_key(farm_id, data.idempotency_key)
            if replay is not None:
                return replay, False
            raise ConflictError("Material consumption conflict") from exc
        except Exception:
            await self.db.rollback()
            raise
        await self.db.refresh(consumption)
        return consumption, True

    async def get(self, farm_id: int, consumption_id: int) -> MaterialConsumption:
        stmt = select(MaterialConsumption).where(
            MaterialConsumption.id == consumption_id,
            MaterialConsumption.farm_id == farm_id,
        )
        row = (await self.db.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise NotFoundError("Material consumption not found")
        return row

    async def update(
        self, farm_id: int, consumption_id: int, data: MaterialConsumptionUpdate
    ) -> MaterialConsumption:
        consumption = await self.get(farm_id, consumption_id)
        updates = data.model_dump(exclude_unset=True)
        try:
            await self._validate_update(farm_id, consumption, updates)
            if _STOCK_FIELDS & updates.keys():
                await self._reconcile_stock(consumption, updates)
            for key, value in updates.items():
                setattr(consumption, key, value)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        await self.db.refresh(consumption)
        return consumption

    async def delete(self, farm_id: int, consumption_id: int) -> None:
        consumption = await self.get(farm_id, consumption_id)
        event = await self.db.get(Event, consumption.inventory_event_id)
        try:
            await self.db.delete(consumption)
            await self.db.flush()
            if event is not None:
                await reverse_decrement(self.db, event=event)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def list_consumptions(
        self,
        *,
        farm_id: int,
        filters: MaterialConsumptionFilters,
        search: str | None,
        sort: str | None,
        page: PageParams,
    ) -> tuple[list[MaterialConsumption], int]:
        stmt = select(MaterialConsumption).where(MaterialConsumption.farm_id == farm_id)
        if filters.material_asset_id is not None:
            stmt = stmt.where(MaterialConsumption.material_asset_id == filters.material_asset_id)
        if filters.consumer_asset_id is not None:
            stmt = stmt.where(MaterialConsumption.consumer_asset_id == filters.consumer_asset_id)
        if filters.reason is not None:
            stmt = stmt.where(MaterialConsumption.reason == filters.reason)
        stmt = apply_date_range(
            stmt, MaterialConsumption.occurred_at, filters.date_from, filters.date_to
        )
        stmt = apply_search(stmt, search, SEARCH_COLUMNS)
        stmt = apply_sort(stmt, sort, SORT_ALLOWED)
        if sort is None:
            stmt = stmt.order_by(
                MaterialConsumption.occurred_at.desc(), MaterialConsumption.id.desc()
            )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(page.offset).limit(page.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total

    async def _validate_create(self, farm_id: int, data: MaterialConsumptionCreate) -> Asset:
        material = await validate_material_asset(self.db, farm_id, data.material_asset_id)
        await validate_consumer(self.db, farm_id, data.consumer_asset_id, data.individual_id)
        await validate_unit_in_stock(self.db, material.id, data.unit)
        return material

    async def _validate_update(
        self, farm_id: int, consumption: MaterialConsumption, updates: dict[str, Any]
    ) -> None:
        reason = updates.get("reason", consumption.reason)
        consumer = updates.get("consumer_asset_id", consumption.consumer_asset_id)
        individual = updates.get("individual_id", consumption.individual_id)
        assert_consumer_rules(reason, consumer, individual)
        if {"consumer_asset_id", "individual_id"} & updates.keys():
            await validate_consumer(self.db, farm_id, consumer, individual)
        if "unit" in updates:
            await validate_unit_in_stock(self.db, consumption.material_asset_id, updates["unit"])

    async def _reconcile_stock(
        self, consumption: MaterialConsumption, updates: dict[str, Any]
    ) -> None:
        event = await self.db.get(Event, consumption.inventory_event_id)
        if event is None:
            raise NotFoundError("Paired inventory event missing")
        await reconcile_decrement(
            self.db,
            material_id=consumption.material_asset_id,
            event=event,
            unit=updates.get("unit", consumption.unit),
            quantity=updates.get("quantity", consumption.quantity),
            occurred_at=updates.get("occurred_at", consumption.occurred_at),
        )

    async def _by_idempotency_key(
        self, farm_id: int, key: str | None
    ) -> MaterialConsumption | None:
        if key is None:
            return None
        stmt = select(MaterialConsumption).where(
            MaterialConsumption.farm_id == farm_id,
            MaterialConsumption.idempotency_key == key,
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()
