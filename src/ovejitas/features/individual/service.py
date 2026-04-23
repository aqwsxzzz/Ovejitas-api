from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError, ValidationError
from ovejitas.core.filters import apply_date_range
from ovejitas.core.pagination import PageParams
from ovejitas.core.search import apply_search
from ovejitas.core.sorting import apply_sort
from ovejitas.features.asset.models import Asset, AssetMode
from ovejitas.features.individual.models import Individual, IndividualStatus
from ovejitas.features.individual.schemas import (
    IndividualCreate,
    IndividualFilters,
    IndividualUpdate,
)

SEARCH_COLUMNS = [Individual.name, Individual.tag]
SORT_ALLOWED = {
    "name": Individual.name,
    "tag": Individual.tag,
    "birth_date": Individual.birth_date,
    "status": Individual.status,
    "created_at": Individual.created_at,
    "updated_at": Individual.updated_at,
}


class IndividualService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, asset: Asset, data: IndividualCreate) -> Individual:
        if asset.mode is not AssetMode.INDIVIDUAL:
            raise ValidationError("Cannot create an individual under an aggregated asset")
        await self._validate_parents(asset.farm_id, data.mother_id, data.father_id)
        individual = Individual(
            farm_id=asset.farm_id,
            asset_id=asset.id,
            status=IndividualStatus.ACTIVE,
            **data.model_dump(),
        )
        self.db.add(individual)
        await self.db.commit()
        await self.db.refresh(individual)
        return individual

    async def get(self, asset_id: int, individual_id: int) -> Individual:
        stmt = select(Individual).where(
            Individual.id == individual_id, Individual.asset_id == asset_id
        )
        individual = (await self.db.execute(stmt)).scalar_one_or_none()
        if individual is None:
            raise NotFoundError("Individual not found")
        return individual

    async def update(self, asset: Asset, individual_id: int, data: IndividualUpdate) -> Individual:
        individual = await self.get(asset.id, individual_id)
        updates = data.model_dump(exclude_unset=True)
        if "mother_id" in updates or "father_id" in updates:
            await self._validate_parents(
                asset.farm_id,
                updates.get("mother_id", individual.mother_id),
                updates.get("father_id", individual.father_id),
            )
        for key, value in updates.items():
            setattr(individual, key, value)
        await self.db.commit()
        await self.db.refresh(individual)
        return individual

    async def delete(self, asset_id: int, individual_id: int) -> None:
        individual = await self.get(asset_id, individual_id)
        await self.db.delete(individual)
        await self.db.commit()

    async def list_individuals(
        self,
        *,
        asset: Asset,
        filters: IndividualFilters,
        search: str | None,
        sort: str | None,
        page: PageParams,
    ) -> tuple[list[Individual], int]:
        stmt = select(Individual).where(Individual.asset_id == asset.id)
        if filters.status is not None:
            stmt = stmt.where(Individual.status == filters.status)
        stmt = apply_date_range(stmt, Individual.created_at, filters.date_from, filters.date_to)
        stmt = apply_search(stmt, search, SEARCH_COLUMNS)
        stmt = apply_sort(stmt, sort, SORT_ALLOWED)
        if sort is None:
            stmt = stmt.order_by(Individual.created_at.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.offset(page.offset).limit(page.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total

    async def _validate_parents(
        self, farm_id: int, mother_id: int | None, father_id: int | None
    ) -> None:
        for parent_id, label in [(mother_id, "mother"), (father_id, "father")]:
            if parent_id is None:
                continue
            stmt = select(Individual).where(
                Individual.id == parent_id, Individual.farm_id == farm_id
            )
            parent = (await self.db.execute(stmt)).scalar_one_or_none()
            if parent is None:
                raise ValidationError(f"{label} not found in this farm")
