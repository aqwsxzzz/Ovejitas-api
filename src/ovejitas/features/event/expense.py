"""Expense-event helper backing material purchases.

A purchase emits an EXPENSE event alongside its inventory increment, so stock
and finances stay connected. These functions create / mutate / delete that
event inside the caller's transaction; the caller owns commit/rollback.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.asset.models import Asset
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType

_PURCHASE_PAYLOAD = {"source": "material_purchase"}


async def emit_expense(
    db: AsyncSession,
    *,
    material: Asset,
    amount: Decimal,
    currency_id: int,
    occurred_at: datetime,
    created_by: int,
) -> Event:
    """Create the EXPENSE event paired with a material purchase."""
    event = Event(
        farm_id=material.farm_id,
        asset_id=material.id,
        type=EventType.EXPENSE,
        occurred_at=occurred_at,
        amount=amount,
        currency_id=currency_id,
        payload=dict(_PURCHASE_PAYLOAD),
        created_by=created_by,
    )
    db.add(event)
    await db.flush()
    return event


async def reconcile_expense(
    db: AsyncSession, *, event: Event, amount: Decimal, occurred_at: datetime
) -> None:
    """Mutate the paired EXPENSE event in place."""
    event.amount = amount
    event.occurred_at = occurred_at
    await db.flush()


async def reverse_expense(db: AsyncSession, *, event: Event) -> None:
    """Delete the paired EXPENSE event."""
    await db.delete(event)
    await db.flush()
