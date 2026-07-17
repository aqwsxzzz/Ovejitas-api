"""The birth action — one real-world act (an animal giving birth) recorded as
one transaction: a REPRODUCTIVE event on the mother, N offspring Individual
rows, and each offspring's ACQUISITION(born) event. Every offspring's
``birth_event_id`` is linked to the shared reproductive event so the litter is
a verifiable fact, not a free-floating count (Philosophy 1).

Self-contained: validates, orchestrates, and commits inside one transaction
with rollback-on-failure. The router calls ``create_birth`` directly. This is
create-only — there is no birth reconcile/reverse; a mistake is corrected by
editing the offspring or the event individually.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError, ValidationError
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.guards import validate_category, validate_type_against_asset
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import AcquisitionMethod, EventType
from ovejitas.features.individual.acquisition import emit_acquisition
from ovejitas.features.individual.models import Individual, IndividualStatus
from ovejitas.features.individual.schemas import BirthCreate, OffspringCreate

_BIRTH_SOURCE = "birth"


async def _load_mother(db: AsyncSession, asset: Asset, mother_id: int) -> Individual:
    stmt = select(Individual).where(Individual.id == mother_id, Individual.asset_id == asset.id)
    mother = (await db.execute(stmt)).scalar_one_or_none()
    if mother is None:
        raise NotFoundError("Mother individual not found")
    return mother


async def _validate_father(
    db: AsyncSession, farm_id: int, mother_id: int, father_id: int | None
) -> None:
    if father_id is None:
        return
    if father_id == mother_id:
        raise ValidationError("Mother and father cannot be the same individual")
    stmt = select(Individual.id).where(Individual.id == father_id, Individual.farm_id == farm_id)
    if (await db.execute(stmt)).scalar_one_or_none() is None:
        raise ValidationError("father not found in this farm")


def _reproductive_event(
    *, mother: Individual, asset: Asset, data: BirthCreate, user_id: int
) -> Event:
    payload: dict[str, str] = {"source": _BIRTH_SOURCE}
    if data.outcome is not None:
        payload["outcome"] = data.outcome
    return Event(
        farm_id=asset.farm_id,
        asset_id=asset.id,
        individual_id=mother.id,
        type=EventType.REPRODUCTIVE,
        occurred_at=data.occurred_at,
        category_id=data.category_id,
        notes=data.notes,
        payload=payload,
        created_by=user_id,
    )


def _offspring_individual(
    *,
    spec: OffspringCreate,
    mother: Individual,
    asset: Asset,
    father_id: int | None,
    occurred_at: datetime,
) -> Individual:
    return Individual(
        farm_id=asset.farm_id,
        asset_id=asset.id,
        tag=spec.tag,
        name=spec.name,
        birth_date=spec.birth_date or occurred_at.date(),
        mother_id=mother.id,
        father_id=father_id,
        status=IndividualStatus.ACTIVE,
        extra=spec.extra,
    )


async def _create_offspring(
    db: AsyncSession,
    *,
    data: BirthCreate,
    mother: Individual,
    asset: Asset,
    reproductive_id: int,
    user_id: int,
) -> list[Individual]:
    """Insert the offspring rows and emit each one's ACQUISITION(born) event."""
    offspring = [
        _offspring_individual(
            spec=spec,
            mother=mother,
            asset=asset,
            father_id=data.father_id,
            occurred_at=data.occurred_at,
        )
        for spec in data.offspring
    ]
    db.add_all(offspring)
    await db.flush()
    for child in offspring:
        acquisition, _ = await emit_acquisition(
            db,
            individual=child,
            asset=asset,
            method=AcquisitionMethod.BORN,
            occurred_at=data.occurred_at,
            amount=None,
            currency_id=None,
            user_id=user_id,
        )
        child.acquisition_event_id = acquisition.id
        child.birth_event_id = reproductive_id
    await db.flush()
    return offspring


async def create_birth(
    db: AsyncSession, *, asset: Asset, mother_id: int, user_id: int, data: BirthCreate
) -> tuple[Event, list[Individual]]:
    """Record a birth: emit the REPRODUCTIVE event and create the offspring."""
    await validate_type_against_asset(EventType.REPRODUCTIVE, asset)
    mother = await _load_mother(db, asset, mother_id)
    if mother.status is not IndividualStatus.ACTIVE:
        raise ValidationError("Only an active mother can give birth")
    await _validate_father(db, asset.farm_id, mother.id, data.father_id)
    await validate_category(db, asset.farm_id, EventType.REPRODUCTIVE, data.category_id)
    try:
        reproductive = _reproductive_event(mother=mother, asset=asset, data=data, user_id=user_id)
        db.add(reproductive)
        await db.flush()
        offspring = await _create_offspring(
            db,
            data=data,
            mother=mother,
            asset=asset,
            reproductive_id=reproductive.id,
            user_id=user_id,
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(reproductive)
    for child in offspring:
        await db.refresh(child)
    return reproductive, offspring
