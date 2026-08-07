"""Working out the due date a pregnancy check should carry.

A positive check that arrives without a due date gets one projected from the
farm's own gestation length, recorded on the animal's asset. The clock starts
at the service date when the farmer knows it; otherwise the check date is the
only base we have, and the result is an estimate rather than a projection.

An asset with no gestation length configured derives nothing — the record
simply carries no due date, exactly as it did before this existed. Derivation
happens on create only, so a stored due date never moves under a farmer who
later edits the flock's gestation length.
"""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.asset.models import Asset
from ovejitas.features.individual.models import Individual
from ovejitas.features.pregnancy.schemas import PregnancyCreate


async def resolve_expected_due_at(
    db: AsyncSession, *, individual: Individual, data: PregnancyCreate
) -> datetime | None:
    """The due date to store: the farmer's if they gave one, otherwise derived."""
    if data.expected_due_at is not None or not data.is_pregnant:
        return data.expected_due_at
    stmt = select(Asset.gestation_days).where(Asset.id == individual.asset_id)
    gestation_days = (await db.execute(stmt)).scalar_one_or_none()
    if gestation_days is None:
        return None
    return (data.service_date or data.occurred_at) + timedelta(days=gestation_days)
