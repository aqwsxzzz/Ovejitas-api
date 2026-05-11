from collections import defaultdict
from decimal import Decimal
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
from ovejitas.features.event.guards import (
    validate_category,
    validate_individual,
    validate_type_against_asset,
)
from ovejitas.features.event.models import Event
from ovejitas.features.event.schemas import (
    EventCreate,
    EventFilters,
    EventUpdate,
    InventoryBalance,
    InventoryBalanceRow,
)
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit
from ovejitas.features.farm.models import Farm

SEARCH_COLUMNS = [Event.notes]
SORT_ALLOWED = {
    "occurred_at": Event.occurred_at,
    "created_at": Event.created_at,
    "updated_at": Event.updated_at,
    "type": Event.type,
}


class EventService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, asset: Asset, user_id: int, data: EventCreate) -> Event:
        await validate_type_against_asset(data.type, asset)
        await validate_individual(self.db, asset, data.individual_id)
        await validate_category(self.db, asset.farm_id, data.type, data.category_id)
        payload = data.model_dump()
        if payload.get("amount") is not None:
            farm = await self.db.get(Farm, asset.farm_id)
            assert farm is not None
            payload["currency"] = farm.default_currency
        event = Event(
            farm_id=asset.farm_id,
            asset_id=asset.id,
            created_by=user_id,
            **payload,
        )
        self.db.add(event)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ConflictError("Idempotency key already used in this farm") from exc
        await self.db.refresh(event)
        return event

    async def get(self, asset_id: int, event_id: int) -> Event:
        stmt = select(Event).where(Event.id == event_id, Event.asset_id == asset_id)
        event = (await self.db.execute(stmt)).scalar_one_or_none()
        if event is None:
            raise NotFoundError("Event not found")
        return event

    async def update(self, asset: Asset, event_id: int, data: EventUpdate) -> Event:
        event = await self.get(asset.id, event_id)
        updates = data.model_dump(exclude_unset=True)
        if "individual_id" in updates:
            await validate_individual(self.db, asset, updates["individual_id"])
        if "category_id" in updates:
            await validate_category(self.db, asset.farm_id, event.type, updates["category_id"])
        if updates.get("amount") is not None and event.currency is None:
            farm = await self.db.get(Farm, asset.farm_id)
            assert farm is not None
            event.currency = farm.default_currency
        for key, value in updates.items():
            setattr(event, key, value)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def delete(self, asset_id: int, event_id: int) -> None:
        event = await self.get(asset_id, event_id)
        await self.db.delete(event)
        await self.db.commit()

    async def list_events(
        self,
        *,
        asset: Asset,
        filters: EventFilters,
        search: str | None,
        sort: str | None,
        page: PageParams,
    ) -> tuple[list[Event], int]:
        stmt = select(Event).where(Event.asset_id == asset.id)
        if filters.type is not None:
            stmt = stmt.where(Event.type == filters.type)
        if filters.category_id is not None:
            stmt = stmt.where(Event.category_id == filters.category_id)
        if filters.individual_id is not None:
            stmt = stmt.where(Event.individual_id == filters.individual_id)
        if filters.adjustment is not None:
            stmt = stmt.where(Event.adjustment == filters.adjustment)
        stmt = apply_date_range(stmt, Event.occurred_at, filters.date_from, filters.date_to)
        stmt = apply_search(stmt, search, SEARCH_COLUMNS)
        stmt = apply_sort(stmt, sort, SORT_ALLOWED)
        if sort is None:
            stmt = stmt.order_by(Event.occurred_at.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.offset(page.offset).limit(page.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total

    async def inventory_balance(self, asset: Asset) -> InventoryBalance:
        stmt = (
            select(Event.adjustment, Event.unit, Event.quantity, Event.occurred_at)
            .where(
                Event.asset_id == asset.id,
                Event.type == EventType.INVENTORY,
            )
            .order_by(Event.occurred_at.asc(), Event.id.asc())
        )
        rows = (await self.db.execute(stmt)).all()
        by_unit: dict[Unit, dict[str, Any]] = defaultdict(
            lambda: {"on_hand": Decimal(0), "last_reset_at": None}
        )
        for adjustment, unit, quantity, occurred_at in rows:
            bucket = by_unit[unit]
            if adjustment is InventoryAdjustment.RESET:
                bucket["on_hand"] = Decimal(quantity)
                bucket["last_reset_at"] = occurred_at
            elif adjustment is InventoryAdjustment.INCREMENT:
                bucket["on_hand"] = bucket["on_hand"] + Decimal(quantity)
            elif adjustment is InventoryAdjustment.DECREMENT:
                bucket["on_hand"] = bucket["on_hand"] - Decimal(quantity)
        balances = [
            InventoryBalanceRow(
                unit=unit,
                on_hand=vals["on_hand"],
                last_reset_at=vals["last_reset_at"],
            )
            for unit, vals in sorted(by_unit.items(), key=lambda kv: kv[0].value)
        ]
        return InventoryBalance(asset_id=asset.id, balances=balances)
