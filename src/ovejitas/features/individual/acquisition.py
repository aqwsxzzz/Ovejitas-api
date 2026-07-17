"""Lifecycle of the events an individual's acquisition owns — the ACQUISITION
event recording its entry into the herd and, when it was purchased, the paired
EXPENSE event booking its cost.

The individual service calls these helpers; it never builds acquisition events
by hand. They emit / reconcile / reverse inside the caller's transaction — the
caller owns commit/rollback.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError, ValidationError
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.expense import reconcile_expense, reverse_expense
from ovejitas.features.event.models import Event
from ovejitas.features.event.reversal import delete_event_if_exists
from ovejitas.features.event.types import AcquisitionMethod, EventType
from ovejitas.features.individual.models import Individual

_ACQUISITION_SOURCE = "acquisition"


def _acquisition_expense_event(
    *,
    individual: Individual,
    asset: Asset,
    amount: Decimal,
    currency_id: int,
    occurred_at: datetime,
    user_id: int,
) -> Event:
    return Event(
        farm_id=asset.farm_id,
        asset_id=asset.id,
        individual_id=individual.id,
        type=EventType.EXPENSE,
        occurred_at=occurred_at,
        amount=amount,
        currency_id=currency_id,
        payload={"source": _ACQUISITION_SOURCE},
        created_by=user_id,
    )


async def emit_acquisition(
    db: AsyncSession,
    *,
    individual: Individual,
    asset: Asset,
    method: AcquisitionMethod,
    occurred_at: datetime,
    amount: Decimal | None,
    currency_id: int | None,
    user_id: int,
) -> tuple[Event, Event | None]:
    """Emit the ACQUISITION event and, when purchased, the paired EXPENSE event.

    ``individual`` must already be flushed so its id is available.
    """
    acquisition = Event(
        farm_id=asset.farm_id,
        asset_id=asset.id,
        individual_id=individual.id,
        type=EventType.ACQUISITION,
        occurred_at=occurred_at,
        quantity=Decimal(1),
        payload={"source": _ACQUISITION_SOURCE, "method": method.value},
        created_by=user_id,
    )
    db.add(acquisition)
    expense: Event | None = None
    if method is AcquisitionMethod.PURCHASED:
        assert amount is not None and currency_id is not None
        expense = _acquisition_expense_event(
            individual=individual,
            asset=asset,
            amount=amount,
            currency_id=currency_id,
            occurred_at=occurred_at,
            user_id=user_id,
        )
        db.add(expense)
    await db.flush()
    return acquisition, expense


async def reconcile_acquisition(
    db: AsyncSession,
    *,
    individual: Individual,
    asset: Asset,
    updates: dict[str, Any],
    currency_id: int,
    user_id: int,
) -> None:
    """Sync the acquisition event (and paired expense) to the updated fields.

    ``updates`` holds only the acquisition keys actually sent in the PATCH.
    """
    acquisition = await db.get(Event, individual.acquisition_event_id)
    if acquisition is None:
        raise NotFoundError("Paired acquisition event missing")
    occurred_at = updates.get("acquired_at", acquisition.occurred_at)
    method = updates.get("acquisition_method") or AcquisitionMethod(acquisition.payload["method"])
    acquisition.occurred_at = occurred_at
    acquisition.payload = {**acquisition.payload, "method": method.value}
    await _reconcile_expense_side(
        db,
        individual=individual,
        asset=asset,
        updates=updates,
        method=method,
        occurred_at=occurred_at,
        currency_id=currency_id,
        user_id=user_id,
    )
    await db.flush()


async def _reconcile_expense_side(
    db: AsyncSession,
    *,
    individual: Individual,
    asset: Asset,
    updates: dict[str, Any],
    method: AcquisitionMethod,
    occurred_at: datetime,
    currency_id: int,
    user_id: int,
) -> None:
    expense = (
        await db.get(Event, individual.acquisition_expense_event_id)
        if individual.acquisition_expense_event_id is not None
        else None
    )
    if method is not AcquisitionMethod.PURCHASED:
        if updates.get("amount") is not None:
            raise ValidationError("amount is only valid for a purchased acquisition")
        if expense is not None:
            individual.acquisition_expense_event_id = None
            await db.flush()
            await reverse_expense(db, event=expense)
        return
    amount = updates.get("amount", expense.amount if expense is not None else None)
    if amount is None:
        raise ValidationError("amount is required for a purchased acquisition")
    if expense is None:
        expense = _acquisition_expense_event(
            individual=individual,
            asset=asset,
            amount=amount,
            currency_id=currency_id,
            occurred_at=occurred_at,
            user_id=user_id,
        )
        db.add(expense)
        await db.flush()
        individual.acquisition_expense_event_id = expense.id
    else:
        await reconcile_expense(db, event=expense, amount=amount, occurred_at=occurred_at)


async def reverse_acquisition(db: AsyncSession, *, individual: Individual) -> None:
    """Detach and delete the acquisition event and any paired expense event.

    The individual's FK columns are cleared and flushed first so deleting the
    events does not trip their RESTRICT foreign keys.
    """
    event_ids = (individual.acquisition_expense_event_id, individual.acquisition_event_id)
    individual.acquisition_event_id = None
    individual.acquisition_expense_event_id = None
    await db.flush()
    for event_id in event_ids:
        await delete_event_if_exists(db, event_id)
    await db.flush()
