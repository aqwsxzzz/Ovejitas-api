"""Reproductive-event helper backing pregnancy records.

A pregnancy owns a REPRODUCTIVE event on the individual's timeline. These
functions create / mutate / delete that event inside the caller's transaction;
the caller owns commit/rollback. The record's fields are mirrored into the
event ``payload`` as a snapshot (datetimes as ISO strings, JSONB-safe), so the
timeline says who bred her and when she was served, not merely that she was
checked.
"""

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.individual.models import Individual
from ovejitas.features.pregnancy.models import Pregnancy

_SOURCE = "pregnancy"


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _payload(pregnancy: Pregnancy) -> dict[str, Any]:
    return {
        "source": _SOURCE,
        "is_pregnant": pregnancy.is_pregnant,
        "offspring_count": pregnancy.offspring_count,
        "expected_due_at": _iso(pregnancy.expected_due_at),
        "service_date": _iso(pregnancy.service_date),
        "sire_individual_id": pregnancy.sire_individual_id,
    }


async def emit_reproductive(
    db: AsyncSession, *, individual: Individual, pregnancy: Pregnancy, created_by: int
) -> Event:
    """Create the REPRODUCTIVE event paired with a pregnancy record."""
    event = Event(
        farm_id=individual.farm_id,
        asset_id=individual.asset_id,
        individual_id=individual.id,
        type=EventType.REPRODUCTIVE,
        occurred_at=pregnancy.occurred_at,
        payload=_payload(pregnancy),
        created_by=created_by,
    )
    db.add(event)
    await db.flush()
    return event


async def reconcile_reproductive(db: AsyncSession, *, event: Event, pregnancy: Pregnancy) -> None:
    """Mutate the paired REPRODUCTIVE event in place to match the record."""
    event.occurred_at = pregnancy.occurred_at
    event.payload = _payload(pregnancy)
    await db.flush()


async def reverse_reproductive(db: AsyncSession, *, event: Event) -> None:
    """Delete the paired REPRODUCTIVE event."""
    await db.delete(event)
    await db.flush()
