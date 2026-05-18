"""Lifecycle of the two events a material purchase owns — the inventory
increment and the expense — kept in sync with the purchase row.

The purchase service calls these to emit / reconcile / reverse the pair; it
never touches event/inventory.py or event/expense.py directly.
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.expense import emit_expense, reconcile_expense, reverse_expense
from ovejitas.features.event.inventory import emit_increment, reconcile_increment, reverse_increment
from ovejitas.features.event.models import Event
from ovejitas.features.material_purchase.models import MaterialPurchase
from ovejitas.features.material_purchase.schemas import MaterialPurchaseCreate

_STOCK_FIELDS = {"quantity", "unit", "occurred_at"}
_EXPENSE_FIELDS = {"amount", "occurred_at"}


async def emit_pair(
    db: AsyncSession,
    *,
    material: Asset,
    data: MaterialPurchaseCreate,
    currency: str,
    user_id: int,
) -> tuple[int, int]:
    """Emit the increment + expense events; return their ids for linking."""
    increment = await emit_increment(
        db,
        material=material,
        unit=data.unit,
        quantity=data.quantity,
        occurred_at=data.occurred_at,
        created_by=user_id,
        source="material_purchase",
    )
    expense = await emit_expense(
        db,
        material=material,
        amount=data.amount,
        currency=currency,
        occurred_at=data.occurred_at,
        created_by=user_id,
    )
    return increment.id, expense.id


async def reconcile_pair(
    db: AsyncSession, *, purchase: MaterialPurchase, updates: dict[str, Any]
) -> None:
    """Sync each paired event to the purchase's updated fields."""
    if _STOCK_FIELDS & updates.keys():
        increment = await db.get(Event, purchase.inventory_event_id)
        if increment is None:
            raise NotFoundError("Paired inventory event missing")
        await reconcile_increment(
            db,
            material_id=purchase.material_asset_id,
            event=increment,
            unit=updates.get("unit", purchase.unit),
            quantity=updates.get("quantity", purchase.quantity),
            occurred_at=updates.get("occurred_at", purchase.occurred_at),
        )
    if _EXPENSE_FIELDS & updates.keys():
        expense = await db.get(Event, purchase.expense_event_id)
        if expense is None:
            raise NotFoundError("Paired expense event missing")
        await reconcile_expense(
            db,
            event=expense,
            amount=updates.get("amount", purchase.amount),
            occurred_at=updates.get("occurred_at", purchase.occurred_at),
        )


async def reverse_pair(
    db: AsyncSession,
    *,
    material_asset_id: int,
    inventory_event_id: int,
    expense_event_id: int,
) -> None:
    """Delete both paired events. Reversing the increment can oversell stock."""
    expense = await db.get(Event, expense_event_id)
    if expense is not None:
        await reverse_expense(db, event=expense)
    increment = await db.get(Event, inventory_event_id)
    if increment is not None:
        await reverse_increment(db, material_id=material_asset_id, event=increment)
