"""Lifecycle of the MORTALITY event an individual owns — the closing entry in
its ledger, emitted when its status transitions to ``deceased``.

The individual service calls these helpers; it never builds mortality events by
hand. They emit / reconcile / reverse inside the caller's transaction — the
caller owns commit/rollback.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError, ValidationError
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.models import Event
from ovejitas.features.event.reversal import delete_event_if_exists
from ovejitas.features.event.types import EventType
from ovejitas.features.individual.models import Individual, IndividualStatus

_MORTALITY_SOURCE = "mortality"


async def emit_mortality(
    db: AsyncSession,
    *,
    individual: Individual,
    asset: Asset,
    occurred_at: datetime,
    cause: str | None,
    user_id: int,
) -> Event:
    """Emit the MORTALITY event. ``individual`` must already be flushed."""
    mortality = Event(
        farm_id=asset.farm_id,
        asset_id=asset.id,
        individual_id=individual.id,
        type=EventType.MORTALITY,
        occurred_at=occurred_at,
        quantity=Decimal(1),
        notes=cause,
        payload={"source": _MORTALITY_SOURCE},
        created_by=user_id,
    )
    db.add(mortality)
    await db.flush()
    return mortality


async def reconcile_mortality(
    db: AsyncSession, *, individual: Individual, updates: dict[str, Any]
) -> None:
    """Sync the mortality event to edited death details.

    ``updates`` holds only the mortality keys actually sent in the PATCH.
    """
    mortality = await db.get(Event, individual.mortality_event_id)
    if mortality is None:
        raise NotFoundError("Paired mortality event missing")
    if "died_at" in updates:
        mortality.occurred_at = updates["died_at"]
    if "cause" in updates:
        mortality.notes = updates["cause"]
    await db.flush()


async def reverse_mortality(db: AsyncSession, *, individual: Individual) -> None:
    """Detach and delete the mortality event.

    The individual's FK column is cleared and flushed first so deleting the
    event does not trip its RESTRICT foreign key.
    """
    event_id = individual.mortality_event_id
    individual.mortality_event_id = None
    await db.flush()
    await delete_event_if_exists(db, event_id)
    await db.flush()


async def apply_mortality(
    db: AsyncSession,
    *,
    asset: Asset,
    individual: Individual,
    new_status: IndividualStatus | None,
    updates: dict[str, Any],
    user_id: int,
) -> None:
    """Emit, reconcile, or reverse the mortality event for a status change.

    Must run before ``individual.status`` is reassigned — it reads the current
    status to detect the transition.
    """
    was_deceased = individual.status is IndividualStatus.DECEASED
    will_be_deceased = (
        new_status is IndividualStatus.DECEASED if new_status is not None else was_deceased
    )
    if not will_be_deceased:
        if updates:
            raise ValidationError("died_at/cause are only valid for a deceased individual")
        if was_deceased:
            await reverse_mortality(db, individual=individual)
        return
    if not was_deceased:
        event = await emit_mortality(
            db,
            individual=individual,
            asset=asset,
            occurred_at=updates.get("died_at") or datetime.now(UTC),
            cause=updates.get("cause"),
            user_id=user_id,
        )
        individual.mortality_event_id = event.id
    elif updates:
        await reconcile_mortality(db, individual=individual, updates=updates)
