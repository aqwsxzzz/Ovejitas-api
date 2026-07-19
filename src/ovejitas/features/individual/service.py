from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError, ValidationError
from ovejitas.core.filters import apply_date_range
from ovejitas.core.pagination import PageParams
from ovejitas.core.search import apply_search
from ovejitas.core.sorting import apply_sort
from ovejitas.features.asset.models import Asset, AssetMode
from ovejitas.features.currency.service import CurrencyService
from ovejitas.features.event.types import AcquisitionMethod
from ovejitas.features.individual.acquisition import (
    emit_acquisition,
    reconcile_acquisition,
    reverse_acquisition,
)
from ovejitas.features.individual.models import Individual, IndividualStatus
from ovejitas.features.individual.mortality import apply_mortality, reverse_mortality
from ovejitas.features.individual.sale import apply_sale, reverse_sale
from ovejitas.features.individual.schemas import (
    IndividualCreate,
    IndividualFilters,
    IndividualUpdate,
)

_ACQUISITION_INPUT = {"acquired_at", "acquisition_method", "amount"}
_MORTALITY_INPUT = {"died_at", "cause"}
_SALE_INPUT = {"sale_amount", "sold_at", "buyer"}

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

    async def create(self, asset: Asset, user_id: int, data: IndividualCreate) -> Individual:
        if asset.mode is not AssetMode.INDIVIDUAL:
            raise ValidationError("Cannot create an individual under an aggregated asset")
        await self._validate_parents(asset.farm_id, data.mother_id, data.father_id)
        currency_id = (
            await CurrencyService(self.db).resolve_or_default(asset.farm_id, data.currency_id)
            if data.acquisition_method is AcquisitionMethod.PURCHASED
            else None
        )
        individual = Individual(
            farm_id=asset.farm_id,
            asset_id=asset.id,
            status=IndividualStatus.ACTIVE,
            **data.model_dump(exclude=_ACQUISITION_INPUT | {"currency_id"}),
        )
        self.db.add(individual)
        try:
            await self.db.flush()
            acquisition, expense = await emit_acquisition(
                self.db,
                individual=individual,
                asset=asset,
                method=data.acquisition_method,
                occurred_at=data.acquired_at,
                amount=data.amount,
                currency_id=currency_id,
                user_id=user_id,
            )
            individual.acquisition_event_id = acquisition.id
            individual.acquisition_expense_event_id = expense.id if expense is not None else None
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
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

    async def update(
        self, asset: Asset, individual_id: int, user_id: int, data: IndividualUpdate
    ) -> Individual:
        individual = await self.get(asset.id, individual_id)
        updates = data.model_dump(exclude_unset=True)
        if "mother_id" in updates or "father_id" in updates:
            mother = updates.get("mother_id", individual.mother_id)
            father = updates.get("father_id", individual.father_id)
            if mother == individual.id or father == individual.id:
                raise ValidationError("An individual cannot be its own parent")
            if mother is not None and mother == father:
                raise ValidationError("Mother and father cannot be the same individual")
            await self._validate_parents(asset.farm_id, mother, father)
        chosen_currency_id = updates.pop("currency_id", None)
        acquisition_updates = {k: updates.pop(k) for k in _ACQUISITION_INPUT if k in updates}
        mortality_updates = {k: updates.pop(k) for k in _MORTALITY_INPUT if k in updates}
        sale_updates = {k: updates.pop(k) for k in _SALE_INPUT if k in updates}
        new_status = updates.get("status")
        try:
            currency_id = await CurrencyService(self.db).resolve_or_default(
                asset.farm_id, chosen_currency_id
            )
            if acquisition_updates:
                await reconcile_acquisition(
                    self.db,
                    individual=individual,
                    asset=asset,
                    updates=acquisition_updates,
                    currency_id=currency_id,
                    user_id=user_id,
                )
            await apply_mortality(
                self.db,
                asset=asset,
                individual=individual,
                new_status=new_status,
                updates=mortality_updates,
                user_id=user_id,
            )
            await apply_sale(
                self.db,
                asset=asset,
                individual=individual,
                new_status=new_status,
                updates=sale_updates,
                currency_id=currency_id,
                user_id=user_id,
            )
            for key, value in updates.items():
                setattr(individual, key, value)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        await self.db.refresh(individual)
        return individual

    async def delete(self, asset_id: int, individual_id: int) -> None:
        individual = await self.get(asset_id, individual_id)
        try:
            await reverse_acquisition(self.db, individual=individual)
            await reverse_mortality(self.db, individual=individual)
            await reverse_sale(self.db, individual=individual)
            await self.db.delete(individual)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

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
