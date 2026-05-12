from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError
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
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(farm, key, value)
        await self.db.commit()
        await self.db.refresh(farm)
        return farm
