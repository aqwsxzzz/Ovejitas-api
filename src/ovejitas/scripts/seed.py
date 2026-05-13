"""Seed a demo farm: gallinas (aggregated) + vacas (individual, 3 with parentage).

Idempotent by owner email. Re-run replaces nothing: if the email already exists,
the script exits without touching the DB.

Usage: docker compose exec app uv run python -m ovejitas.scripts.seed
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import ovejitas.models  # noqa: F401  — register every model on Base.metadata
from ovejitas.core.config import get_settings
from ovejitas.core.db import engine, session_factory
from ovejitas.core.security import hash_password
from ovejitas.features.asset.models import Asset, AssetKind, AssetMode
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, InventoryAdjustment
from ovejitas.features.farm.models import Farm
from ovejitas.features.farm_member.models import FarmMember, FarmRole
from ovejitas.features.individual.models import Individual, IndividualStatus
from ovejitas.features.user.models import User

logger = logging.getLogger("ovejitas.seed")
logging.basicConfig(level=logging.INFO, format="%(message)s")

DEMO_EMAIL = "demo@ovejitas.app"
DEMO_PASSWORD = "demo-password"
DEMO_FARM_NAME = "Granja Demo"
TODAY = datetime(2026, 4, 20, 12, 0, tzinfo=UTC)


async def _already_seeded(db: AsyncSession) -> bool:
    stmt = select(User.id).where(User.email == DEMO_EMAIL)
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def _seed_user_and_farm(db: AsyncSession) -> tuple[User, Farm]:
    user = User(email=DEMO_EMAIL, name="Demo", password_hash=hash_password(DEMO_PASSWORD))
    farm = Farm(name=DEMO_FARM_NAME, default_currency="USD")
    db.add_all([user, farm])
    await db.flush()
    db.add(FarmMember(user_id=user.id, farm_id=farm.id, role=FarmRole.OWNER))
    await db.flush()
    return user, farm


async def _seed_gallinas(db: AsyncSession, user: User, farm: Farm) -> None:
    asset = Asset(
        farm_id=farm.id,
        name="Gallinas ponedoras",
        kind=AssetKind.ANIMAL,
        mode=AssetMode.AGGREGATED,
        location="Galpón norte",
    )
    db.add(asset)
    await db.flush()

    db.add_all(
        [
            Event(
                farm_id=farm.id,
                asset_id=asset.id,
                type=EventType.EXPENSE,
                occurred_at=TODAY - timedelta(days=30),
                amount=Decimal("1500.00"),
                currency="USD",
                payload={"vendor": "Avícola X", "invoice_no": "A-123"},
                created_by=user.id,
            ),
            Event(
                farm_id=farm.id,
                asset_id=asset.id,
                type=EventType.OBSERVATION,
                occurred_at=TODAY - timedelta(days=30),
                quantity=Decimal("200"),
                unit="unit",
                notes="Headcount inicial",
                created_by=user.id,
            ),
        ]
    )
    for offset in range(0, 14):
        db.add(
            Event(
                farm_id=farm.id,
                asset_id=asset.id,
                type=EventType.PRODUCTION,
                occurred_at=TODAY - timedelta(days=offset),
                quantity=Decimal(180 + offset % 5),
                unit="unit",
                created_by=user.id,
            )
        )


async def _seed_vacas(db: AsyncSession, user: User, farm: Farm) -> list[Individual]:
    asset = Asset(
        farm_id=farm.id,
        name="Vacas lecheras",
        kind=AssetKind.ANIMAL,
        mode=AssetMode.INDIVIDUAL,
        location="Potrero sur",
    )
    db.add(asset)
    await db.flush()

    mother = Individual(
        farm_id=farm.id,
        asset_id=asset.id,
        name="Vaca A",
        tag="MX-001",
        birth_date=(TODAY - timedelta(days=365 * 4)).date(),
        status=IndividualStatus.ACTIVE,
        extra={"breed": "Holando"},
    )
    father = Individual(
        farm_id=farm.id,
        asset_id=asset.id,
        name="Toro B",
        tag="MX-002",
        birth_date=(TODAY - timedelta(days=365 * 5)).date(),
        status=IndividualStatus.ACTIVE,
        extra={"breed": "Angus"},
    )
    db.add_all([mother, father])
    await db.flush()

    calf = Individual(
        farm_id=farm.id,
        asset_id=asset.id,
        name="Ternera C",
        tag="MX-003",
        birth_date=(TODAY - timedelta(days=60)).date(),
        mother_id=mother.id,
        father_id=father.id,
        status=IndividualStatus.ACTIVE,
        extra={"breed": "Cruza"},
    )
    db.add(calf)
    await db.flush()

    db.add(
        Event(
            farm_id=farm.id,
            asset_id=asset.id,
            type=EventType.REPRODUCTIVE,
            occurred_at=TODAY - timedelta(days=60),
            individual_id=mother.id,
            payload={"outcome": "live_birth", "offspring_count": 1},
            created_by=user.id,
        )
    )
    for offset in range(0, 7):
        db.add(
            Event(
                farm_id=farm.id,
                asset_id=asset.id,
                type=EventType.PRODUCTION,
                occurred_at=TODAY - timedelta(days=offset),
                individual_id=mother.id,
                quantity=Decimal("18.5"),
                unit="l",
                created_by=user.id,
            )
        )
    return [mother, father, calf]


async def _seed_feed_stock(db: AsyncSession, user: User, farm: Farm) -> None:
    asset = Asset(
        farm_id=farm.id,
        name="Maíz molido",
        kind=AssetKind.MATERIAL,
        mode=AssetMode.AGGREGATED,
        location="Silo principal",
    )
    db.add(asset)
    await db.flush()

    db.add_all(
        [
            Event(
                farm_id=farm.id,
                asset_id=asset.id,
                type=EventType.INVENTORY,
                adjustment=InventoryAdjustment.RESET,
                occurred_at=TODAY - timedelta(days=20),
                quantity=Decimal("500"),
                unit="kg",
                notes="Saldo inicial",
                created_by=user.id,
            ),
            Event(
                farm_id=farm.id,
                asset_id=asset.id,
                type=EventType.INVENTORY,
                adjustment=InventoryAdjustment.INCREMENT,
                occurred_at=TODAY - timedelta(days=10),
                quantity=Decimal("250"),
                unit="kg",
                notes="Compra mensual",
                created_by=user.id,
            ),
            Event(
                farm_id=farm.id,
                asset_id=asset.id,
                type=EventType.INVENTORY,
                adjustment=InventoryAdjustment.DECREMENT,
                occurred_at=TODAY - timedelta(days=2),
                quantity=Decimal("75"),
                unit="kg",
                notes="Consumo semanal",
                created_by=user.id,
            ),
        ]
    )


async def seed() -> None:
    env = get_settings().app_env
    if env != "development":
        raise SystemExit(
            f"seed.py refuses to run with APP_ENV={env!r}. "
            "This script creates a known-credential demo account and only "
            "runs when APP_ENV='development'."
        )
    async with session_factory() as db:
        if await _already_seeded(db):
            logger.info("Seed already applied (user %s exists). Nothing to do.", DEMO_EMAIL)
            return
        user, farm = await _seed_user_and_farm(db)
        await _seed_gallinas(db, user, farm)
        await _seed_vacas(db, user, farm)
        await _seed_feed_stock(db, user, farm)
        await db.commit()
        logger.info("Seed complete — login as %s / %s", DEMO_EMAIL, DEMO_PASSWORD)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
