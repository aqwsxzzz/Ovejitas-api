"""The farm's local timezone — the anchor for every calendar-day boundary the
API draws: report windows, list filters, and produce-pool basket grain."""

from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AfterValidator, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.farm.models import Farm


def _known_zone(name: str) -> str:
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"unknown timezone {name!r} (expected an IANA name)") from exc
    return name


# Allowlist by construction: only a name the tz database resolves is accepted,
# so nothing arbitrary reaches ZoneInfo at report time or AT TIME ZONE in SQL.
IanaTimezone = Annotated[str, Field(min_length=1, max_length=64), AfterValidator(_known_zone)]


async def farm_timezone(db: AsyncSession, farm_id: int) -> ZoneInfo:
    """The farm's local timezone, defaulting to UTC if the farm is gone.

    The stored name is validated on write (FarmUpdate), so it always resolves.
    """
    name = (await db.execute(select(Farm.timezone).where(Farm.id == farm_id))).scalar_one_or_none()
    return ZoneInfo(name or "UTC")
