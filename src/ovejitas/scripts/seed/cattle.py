"""Cattle scene — exercises the individual-asset lifecycle: individual
acquisition, a birth action, sale and mortality transitions, milk harvest from
an individual-mode herd, and a couple of plain manual events. Every row is
emitted through an action or the event service.
"""

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.asset.models import AssetKind, AssetMode
from ovejitas.features.asset.schemas import AssetCreate, AssetUpdate
from ovejitas.features.asset.service import AssetService
from ovejitas.features.event.schemas import EventExpenseCreate, EventObservationCreate
from ovejitas.features.event.service import EventService
from ovejitas.features.event.types import AcquisitionMethod, EventType, Unit
from ovejitas.features.event_category.schemas import EventCategoryCreate
from ovejitas.features.event_category.service import EventCategoryService
from ovejitas.features.farm.models import Farm
from ovejitas.features.harvest.actions import create_harvest
from ovejitas.features.harvest.schemas import HarvestCreate
from ovejitas.features.individual.birth import create_birth
from ovejitas.features.individual.models import IndividualStatus
from ovejitas.features.individual.schemas import (
    BirthCreate,
    IndividualCreate,
    IndividualUpdate,
    OffspringCreate,
)
from ovejitas.features.individual.service import IndividualService
from ovejitas.features.user.models import User


async def seed_cattle(db: AsyncSession, user: User, farm: Farm, today: datetime) -> None:
    assets = AssetService(db)
    herd = await assets.create(
        farm.id,
        AssetCreate(
            name="Vacas lecheras",
            kind=AssetKind.ANIMAL,
            mode=AssetMode.INDIVIDUAL,
            location="Potrero sur",
        ),
    )
    # The product provisions the pool that holds its stock — "Leche" is created
    # once, as a category, and the produce asset comes with it.
    milk_category = await EventCategoryService(db).create(
        farm.id,
        EventCategoryCreate(type=EventType.PRODUCTION, name="Leche", unit=Unit.L),
    )
    assert milk_category.produce_asset_id is not None
    milk = await assets.get(farm.id, milk_category.produce_asset_id)
    herd = await assets.update(farm.id, herd.id, AssetUpdate(produce_asset_id=milk.id))

    individuals = IndividualService(db)
    mother = await individuals.create(
        herd,
        user.id,
        IndividualCreate(
            tag="MX-001",
            name="Vaca A",
            birth_date=(today - timedelta(days=1700)).date(),
            acquisition_method=AcquisitionMethod.PURCHASED,
            amount=Decimal("1200"),
            acquired_at=today - timedelta(days=900),
            extra={"breed": "Holando"},
        ),
    )
    father = await individuals.create(
        herd,
        user.id,
        IndividualCreate(
            tag="MX-002",
            name="Toro B",
            acquisition_method=AcquisitionMethod.PURCHASED,
            amount=Decimal("1500"),
            acquired_at=today - timedelta(days=900),
            extra={"breed": "Angus"},
        ),
    )
    deceased = await individuals.create(
        herd, user.id, IndividualCreate(tag="MX-005", name="Vaca E")
    )
    sold = await individuals.create(herd, user.id, IndividualCreate(tag="MX-006", name="Vaca F"))

    # a birth: Vaca A calves — emits the reproductive event + the calf's
    # acquisition(born), with parentage wired in
    await create_birth(
        db,
        asset=herd,
        mother_id=mother.id,
        user_id=user.id,
        data=BirthCreate(
            occurred_at=today - timedelta(days=60),
            father_id=father.id,
            outcome="live_birth",
            offspring=[OffspringCreate(tag="MX-003", name="Ternera C")],
        ),
    )

    await individuals.update(
        herd,
        deceased.id,
        user.id,
        IndividualUpdate(
            status=IndividualStatus.DECEASED,
            died_at=today - timedelta(days=20),
            cause="Enfermedad",
        ),
    )
    await individuals.update(
        herd,
        sold.id,
        user.id,
        IndividualUpdate(
            status=IndividualStatus.SOLD,
            sale_amount=Decimal("950"),
            sold_at=today - timedelta(days=10),
            buyer="Remate Regional",
        ),
    )

    for offset in range(7, 0, -1):
        await create_harvest(
            db,
            asset=herd,
            user_id=user.id,
            data=HarvestCreate(
                occurred_at=today - timedelta(days=offset),
                quantity=Decimal("18.5"),
                unit=Unit.L,
                category_id=milk_category.id,
            ),
        )

    events = EventService(db)
    await events.create(
        herd,
        user.id,
        EventObservationCreate(
            type=EventType.OBSERVATION,
            occurred_at=today - timedelta(days=15),
            individual_id=mother.id,
            notes="Control veterinario — sin novedades",
        ),
    )
    await events.create(
        herd,
        user.id,
        EventExpenseCreate(
            type=EventType.EXPENSE,
            occurred_at=today - timedelta(days=15),
            amount=Decimal("80"),
            notes="Visita veterinaria",
        ),
    )
