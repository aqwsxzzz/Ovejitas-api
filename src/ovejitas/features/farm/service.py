from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError
from ovejitas.features.currency.models import Currency
from ovejitas.features.farm.models import Farm
from ovejitas.features.farm.schemas import FarmUpdate


class FarmService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, farm_id: int) -> Farm:
        farm = await self.db.get(Farm, farm_id)
        if farm is None:
            raise NotFoundError("Farm not found")
        return farm

    async def update(self, farm_id: int, data: FarmUpdate) -> Farm:
        farm = await self.get(farm_id)
        updates = data.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(farm, key, value)
        if updates.get("default_currency") is not None:
            await self._ensure_currency(farm_id, updates["default_currency"])
        await self.db.commit()
        await self.db.refresh(farm)
        return farm

    async def _ensure_currency(self, farm_id: int, code: str) -> None:
        """Guarantee the preferred currency has a backing row so per-entry
        defaulting always resolves. Idempotent."""
        stmt = select(Currency).where(Currency.farm_id == farm_id, Currency.code == code)
        if (await self.db.execute(stmt)).scalar_one_or_none() is None:
            self.db.add(Currency(farm_id=farm_id, code=code, name=code))
            await self.db.flush()
