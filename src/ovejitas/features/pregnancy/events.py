"""Reproductive-event helper backing pregnancy records.

A pregnancy owns a REPRODUCTIVE event on the individual's timeline. These
functions create / mutate / delete that event inside the caller's transaction;
the caller owns commit/rollback. The structured fields are mirrored into the
event ``payload`` as a snapshot (datetimes as ISO strings, JSONB-safe).
"""

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.individual.models import Individual

_SOURCE = "pregnancy"


def _payload(
    is_pregnant: bool, offspring_count: int | None, expected_due_at: datetime | None
) -> dict[str, Any]:
    return {
        "source": _SOURCE,
        "is_pregnant": is_pregnant,
        "offspring_count": offspring_count,
        "expected_due_at": expected_due_at.isoformat() if expected_due_at is not None else None,
    }


async def emit_reproductive(
    db: AsyncSession,
    *,
    individual: Individual,
    occurred_at: datetime,
    is_pregnant: bool,
    offspring_count: int | None,
    expected_due_at: datetime | None,
    created_by: int,
) -> Event:
    """Create the REPRODUCTIVE event paired with a pregnancy record."""
    event = Event(
        farm_id=individual.farm_id,
        asset_id=individual.asset_id,
        individual_id=individual.id,
        type=EventType.REPRODUCTIVE,
        occurred_at=occurred_at,
        payload=_payload(is_pregnant, offspring_count, expected_due_at),
        created_by=created_by,
    )
    db.add(event)
    await db.flush()
    return event


async def reconcile_reproductive(
    db: AsyncSession,
    *,
    event: Event,
    occurred_at: datetime,
    is_pregnant: bool,
    offspring_count: int | None,
    expected_due_at: datetime | None,
) -> None:
    """Mutate the paired REPRODUCTIVE event in place to match the record."""
    event.occurred_at = occurred_at
    event.payload = _payload(is_pregnant, offspring_count, expected_due_at)
    await db.flush()


async def reverse_reproductive(db: AsyncSession, *, event: Event) -> None:
    """Delete the paired REPRODUCTIVE event."""
    await db.delete(event)
    await db.flush()
