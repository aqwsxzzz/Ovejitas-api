from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ConflictError, NotFoundError, ValidationError
from ovejitas.core.filters import apply_date_range
from ovejitas.core.pagination import PageParams
from ovejitas.core.search import apply_search
from ovejitas.core.sorting import apply_sort
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.balance import compute_inventory_balance
from ovejitas.features.event.guards import (
    assert_fields_valid_for_type,
    validate_category,
    validate_individual,
    validate_type_against_asset,
)
from ovejitas.features.event.inventory import assert_non_negative, lock_material
from ovejitas.features.event.models import Event
from ovejitas.features.event.schemas import EventCreate, EventFilters, EventUpdate, InventoryBalance
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit
from ovejitas.features.farm.models import Farm

SEARCH_COLUMNS = [Event.notes]
SORT_ALLOWED = {
    "occurred_at": Event.occurred_at,
    "created_at": Event.created_at,
    "updated_at": Event.updated_at,
    "type": Event.type,
}


def _assert_not_action_owned(event: Event, verb: str) -> None:
    """Events tagged with a payload.source were emitted by an action and own a
    balance or FK invariant the generic event endpoint cannot safely maintain."""
    if event.payload.get("source"):
        raise ValidationError(f"This event is emitted by an action and cannot be {verb} directly")


class EventService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, asset: Asset, user_id: int, data: EventCreate) -> Event:
        await validate_type_against_asset(data.type, asset)
        await validate_individual(self.db, asset, data.individual_id)
        unit: Unit | None = getattr(data, "unit", None)
        await validate_category(self.db, asset.farm_id, data.type, data.category_id, unit)
        fields = data.model_dump()
        if "source" in fields["payload"]:
            raise ValidationError("payload.source is reserved for action-emitted events")
        if fields.get("amount") is not None:
            farm = await self.db.get(Farm, asset.farm_id)
            assert farm is not None
            fields["currency"] = farm.default_currency
        event = Event(farm_id=asset.farm_id, asset_id=asset.id, created_by=user_id, **fields)
        # A hand-written inventory decrement must respect the same lock + non-negative
        # guard the action layer uses — POST /events is not a backdoor around it.
        is_decrement = (
            data.type is EventType.INVENTORY
            and fields.get("adjustment") is InventoryAdjustment.DECREMENT
        )
        try:
            if is_decrement:
                await lock_material(self.db, asset.id)
            self.db.add(event)
            await self.db.flush()
            if is_decrement:
                await assert_non_negative(self.db, asset.id, fields["unit"])
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ConflictError("Idempotency key already used in this farm") from exc
        except Exception:
            await self.db.rollback()
            raise
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
        _assert_not_action_owned(event, "edited")
        updates = data.model_dump(exclude_unset=True)
        assert_fields_valid_for_type(event.type, updates.keys())
        if "payload" in updates and "source" in updates["payload"]:
            raise ValidationError("payload.source is reserved for action-emitted events")
        if "individual_id" in updates:
            await validate_individual(self.db, asset, updates["individual_id"])
        if "category_id" in updates:
            unit: Unit | None = updates.get("unit", event.unit)
            await validate_category(
                self.db, asset.farm_id, event.type, updates["category_id"], unit
            )
        if updates.get("amount") is not None and event.currency is None:
            farm = await self.db.get(Farm, asset.farm_id)
            assert farm is not None
            event.currency = farm.default_currency
        stock_fields = {"quantity", "unit", "adjustment", "occurred_at"}
        stock_affecting = event.type is EventType.INVENTORY and bool(stock_fields & updates.keys())
        old_unit = event.unit
        try:
            if stock_affecting:
                await lock_material(self.db, asset.id)
            for key, value in updates.items():
                setattr(event, key, value)
            await self.db.flush()
            if stock_affecting and event.unit is not None:
                await assert_non_negative(self.db, asset.id, event.unit)
                if old_unit is not None and old_unit != event.unit:
                    await assert_non_negative(self.db, asset.id, old_unit)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        await self.db.refresh(event)
        return event

    async def delete(self, asset_id: int, event_id: int) -> None:
        event = await self.get(asset_id, event_id)
        _assert_not_action_owned(event, "deleted")
        is_inventory = event.type is EventType.INVENTORY
        unit = event.unit
        try:
            if is_inventory:
                await lock_material(self.db, asset_id)
            await self.db.delete(event)
            await self.db.flush()
            if is_inventory and unit is not None:
                await assert_non_negative(self.db, asset_id, unit)
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ConflictError(
                "Event is referenced by another record and cannot be deleted"
            ) from exc
        except Exception:
            await self.db.rollback()
            raise

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
        return await compute_inventory_balance(self.db, asset)
