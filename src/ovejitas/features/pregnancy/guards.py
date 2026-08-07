"""Validation for pregnancy records.

``assert_pregnancy_projection`` is a pure cross-field check shared by the create
schema and the update service path; ``validate_individual`` and ``validate_sire``
hit the DB to confirm the referenced animals belong to the farm.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError, ValidationError
from ovejitas.features.individual.models import Individual


def assert_pregnancy_projection(
    is_pregnant: bool,
    offspring_count: int | None,
    expected_due_at: object | None,
) -> None:
    """A non-pregnant check projects nothing — no offspring count, no due date."""
    if not is_pregnant and (offspring_count is not None or expected_due_at is not None):
        raise ValidationError("A non-pregnant record cannot carry an offspring count or due date")


async def validate_sire(
    db: AsyncSession, farm_id: int, individual_id: int, sire_individual_id: int | None
) -> None:
    """The sire must be some other animal on this same farm."""
    if sire_individual_id is None:
        return
    if sire_individual_id == individual_id:
        raise ValidationError("The sire cannot be the pregnant individual")
    stmt = select(Individual.id).where(
        Individual.id == sire_individual_id,
        Individual.farm_id == farm_id,
    )
    if (await db.execute(stmt)).scalar_one_or_none() is None:
        raise ValidationError("Sire not found in this farm")


async def validate_individual(db: AsyncSession, farm_id: int, individual_id: int) -> Individual:
    stmt = select(Individual).where(
        Individual.id == individual_id,
        Individual.farm_id == farm_id,
    )
    individual = (await db.execute(stmt)).scalar_one_or_none()
    if individual is None:
        raise NotFoundError("Individual not found")
    return individual
