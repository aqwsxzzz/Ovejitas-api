"""Chicken-flock scene — exercises the aggregated-asset actions: flock
acquisition/sale/mortality, harvest into a produce asset, material purchase /
consumption / sale. Every row is emitted through an action, so the demo data
carries proper ``payload.source`` tags, paired events, and reconciling balances.
"""

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.asset.models import AssetKind, AssetMode
from ovejitas.features.asset.schemas import AssetCreate, AssetUpdate
from ovejitas.features.asset.service import AssetService
from ovejitas.features.event.types import EventType, Unit
from ovejitas.features.event_category.schemas import EventCategoryCreate
from ovejitas.features.event_category.service import EventCategoryService
from ovejitas.features.farm.models import Farm
from ovejitas.features.flock.actions import (
    create_flock_acquisition,
    create_flock_mortality,
    create_flock_sale,
)
from ovejitas.features.flock.schemas import (
    FlockAcquisitionCreate,
    FlockMortalityCreate,
    FlockSaleCreate,
)
from ovejitas.features.harvest.actions import create_harvest
from ovejitas.features.harvest.schemas import HarvestCreate
from ovejitas.features.material_consumption.schemas import MaterialConsumptionCreate
from ovejitas.features.material_consumption.service import MaterialConsumptionService
from ovejitas.features.material_consumption.types import ConsumptionReason
from ovejitas.features.material_purchase.schemas import MaterialPurchaseCreate
from ovejitas.features.material_purchase.service import MaterialPurchaseService
from ovejitas.features.material_sale.actions import create_material_sale
from ovejitas.features.material_sale.schemas import MaterialSaleCreate
from ovejitas.features.user.models import User


async def seed_flock(db: AsyncSession, user: User, farm: Farm, today: datetime) -> None:
    assets = AssetService(db)
    flock = await assets.create(
        farm.id,
        AssetCreate(
            name="Gallinas ponedoras",
            kind=AssetKind.ANIMAL,
            mode=AssetMode.AGGREGATED,
            location="Galpón norte",
        ),
    )
    eggs = await assets.create(
        farm.id,
        AssetCreate(name="Huevos", kind=AssetKind.MATERIAL, mode=AssetMode.AGGREGATED),
    )
    feed = await assets.create(
        farm.id,
        AssetCreate(
            name="Maíz molido",
            kind=AssetKind.MATERIAL,
            mode=AssetMode.AGGREGATED,
            location="Silo principal",
        ),
    )
    # link the flock to its produce asset so harvests flow into "Huevos"
    flock = await assets.update(farm.id, flock.id, AssetUpdate(produce_asset_id=eggs.id))

    await create_flock_acquisition(
        db,
        asset=flock,
        user_id=user.id,
        data=FlockAcquisitionCreate(
            occurred_at=today - timedelta(days=60), quantity=200, amount=Decimal("1500")
        ),
    )

    purchases = MaterialPurchaseService(db)
    for offset, qty, amount in ((50, "500", "1000"), (20, "250", "500")):
        await purchases.create(
            farm.id,
            user.id,
            MaterialPurchaseCreate(
                material_asset_id=feed.id,
                occurred_at=today - timedelta(days=offset),
                quantity=Decimal(qty),
                unit=Unit.KG,
                amount=Decimal(amount),
                supplier="Molino Sur",
            ),
        )

    consumptions = MaterialConsumptionService(db)
    for offset in (45, 30, 15, 3):
        await consumptions.create(
            farm.id,
            user.id,
            MaterialConsumptionCreate(
                material_asset_id=feed.id,
                consumer_asset_id=flock.id,
                occurred_at=today - timedelta(days=offset),
                quantity=Decimal("40"),
                unit=Unit.KG,
                reason=ConsumptionReason.FEEDING,
            ),
        )

    egg_category = await EventCategoryService(db).create(
        farm.id,
        EventCategoryCreate(type=EventType.PRODUCTION, name="Huevos", unit=Unit.UNIT),
    )
    for offset in range(14, 0, -1):
        await create_harvest(
            db,
            asset=flock,
            user_id=user.id,
            data=HarvestCreate(
                occurred_at=today - timedelta(days=offset),
                quantity=Decimal(180 + offset % 5),
                unit=Unit.UNIT,
                category_id=egg_category.id,
            ),
        )

    await create_flock_mortality(
        db,
        asset=flock,
        user_id=user.id,
        data=FlockMortalityCreate(
            occurred_at=today - timedelta(days=28), quantity=5, cause="Ataque de zorro"
        ),
    )
    await create_flock_sale(
        db,
        asset=flock,
        user_id=user.id,
        data=FlockSaleCreate(
            occurred_at=today - timedelta(days=12),
            quantity=20,
            amount=Decimal("280"),
            buyer="Mercado local",
        ),
    )
    await create_material_sale(
        db,
        asset=eggs,
        user_id=user.id,
        data=MaterialSaleCreate(
            occurred_at=today - timedelta(days=5),
            quantity=Decimal("1200"),
            unit=Unit.UNIT,
            amount=Decimal("300"),
            buyer="Almacén El Sol",
        ),
    )
