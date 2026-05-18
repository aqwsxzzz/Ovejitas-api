"""The three flock lifecycle actions — acquisition, sale, mortality — for an
aggregated animal asset. Each is one real-world act recorded as one transaction:
an ``inventory`` event mutating the headcount, plus a paired finance/mortality
event. There is no flock table — the event stream is the whole record, with
``payload.source`` tagging which action emitted each event (Philosophy 1).

Create-only: no reconcile/reverse. Each ``create_*`` owns its commit/rollback.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.inventory import emit_decrement, emit_increment, on_hand
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, Unit
from ovejitas.features.farm.models import Farm
from ovejitas.features.flock.guards import validate_flock_asset
from ovejitas.features.flock.schemas import (
    FlockAcquisitionCreate,
    FlockActionRead,
    FlockMortalityCreate,
    FlockSaleCreate,
)

_ACQUISITION_SOURCE = "flock_acquisition"
_SALE_SOURCE = "flock_sale"
_MORTALITY_SOURCE = "flock_mortality"


async def _farm_currency(db: AsyncSession, farm_id: int) -> str:
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise NotFoundError("Farm not found")
    return farm.default_currency


def _finance_event(
    *,
    asset: Asset,
    event_type: EventType,
    amount: Decimal,
    currency: str,
    occurred_at: datetime,
    user_id: int,
    payload: dict[str, str],
) -> Event:
    return Event(
        farm_id=asset.farm_id,
        asset_id=asset.id,
        type=event_type,
        occurred_at=occurred_at,
        amount=amount,
        currency=currency,
        payload=payload,
        created_by=user_id,
    )


async def create_flock_acquisition(
    db: AsyncSession, *, asset: Asset, user_id: int, data: FlockAcquisitionCreate
) -> FlockActionRead:
    """Increment the flock headcount; book a paired expense when an amount is paid."""
    validate_flock_asset(asset)
    try:
        increment = await emit_increment(
            db,
            material=asset,
            unit=Unit.HEAD,
            quantity=Decimal(data.quantity),
            occurred_at=data.occurred_at,
            created_by=user_id,
            source=_ACQUISITION_SOURCE,
        )
        expense_id: int | None = None
        if data.amount is not None:
            currency = await _farm_currency(db, asset.farm_id)
            expense = _finance_event(
                asset=asset,
                event_type=EventType.EXPENSE,
                amount=data.amount,
                currency=currency,
                occurred_at=data.occurred_at,
                user_id=user_id,
                payload={"source": _ACQUISITION_SOURCE},
            )
            db.add(expense)
            await db.flush()
            expense_id = expense.id
        inventory_event_id = increment.id
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    headcount = await on_hand(db, asset.id, Unit.HEAD)
    return FlockActionRead(
        inventory_event_id=inventory_event_id, paired_event_id=expense_id, headcount=headcount
    )


async def create_flock_sale(
    db: AsyncSession, *, asset: Asset, user_id: int, data: FlockSaleCreate
) -> FlockActionRead:
    """Decrement the flock headcount and book the paired income."""
    validate_flock_asset(asset)
    try:
        decrement = await emit_decrement(
            db,
            material=asset,
            unit=Unit.HEAD,
            quantity=Decimal(data.quantity),
            occurred_at=data.occurred_at,
            created_by=user_id,
            source=_SALE_SOURCE,
        )
        currency = await _farm_currency(db, asset.farm_id)
        payload = {"source": _SALE_SOURCE}
        if data.buyer is not None:
            payload["buyer"] = data.buyer
        income = _finance_event(
            asset=asset,
            event_type=EventType.INCOME,
            amount=data.amount,
            currency=currency,
            occurred_at=data.occurred_at,
            user_id=user_id,
            payload=payload,
        )
        db.add(income)
        await db.flush()
        inventory_event_id, income_id = decrement.id, income.id
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    headcount = await on_hand(db, asset.id, Unit.HEAD)
    return FlockActionRead(
        inventory_event_id=inventory_event_id, paired_event_id=income_id, headcount=headcount
    )


async def create_flock_mortality(
    db: AsyncSession, *, asset: Asset, user_id: int, data: FlockMortalityCreate
) -> FlockActionRead:
    """Decrement the flock headcount and emit a paired mortality event."""
    validate_flock_asset(asset)
    try:
        decrement = await emit_decrement(
            db,
            material=asset,
            unit=Unit.HEAD,
            quantity=Decimal(data.quantity),
            occurred_at=data.occurred_at,
            created_by=user_id,
            source=_MORTALITY_SOURCE,
        )
        mortality = Event(
            farm_id=asset.farm_id,
            asset_id=asset.id,
            type=EventType.MORTALITY,
            occurred_at=data.occurred_at,
            quantity=Decimal(data.quantity),
            notes=data.cause,
            payload={"source": _MORTALITY_SOURCE},
            created_by=user_id,
        )
        db.add(mortality)
        await db.flush()
        inventory_event_id, mortality_id = decrement.id, mortality.id
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    headcount = await on_hand(db, asset.id, Unit.HEAD)
    return FlockActionRead(
        inventory_event_id=inventory_event_id, paired_event_id=mortality_id, headcount=headcount
    )
