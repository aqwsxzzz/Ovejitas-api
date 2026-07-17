from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ConflictError, NotFoundError, ValidationError
from ovejitas.core.filters import apply_date_range
from ovejitas.core.pagination import PageParams
from ovejitas.core.search import apply_search
from ovejitas.core.sorting import apply_sort
from ovejitas.features.currency.models import Currency
from ovejitas.features.currency.schemas import (
    CurrencyCreate,
    CurrencyFilters,
    CurrencyUpdate,
)
from ovejitas.features.farm.models import Farm

SEARCH_COLUMNS = [Currency.code, Currency.name]
SORT_ALLOWED = {
    "code": Currency.code,
    "name": Currency.name,
    "created_at": Currency.created_at,
    "updated_at": Currency.updated_at,
}


class CurrencyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, farm_id: int, data: CurrencyCreate) -> Currency:
        currency = Currency(farm_id=farm_id, **data.model_dump())
        self.db.add(currency)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ConflictError("Currency with this code already exists") from exc
        await self.db.refresh(currency)
        return currency

    async def get(self, farm_id: int, currency_id: int) -> Currency:
        stmt = select(Currency).where(Currency.id == currency_id, Currency.farm_id == farm_id)
        currency = (await self.db.execute(stmt)).scalar_one_or_none()
        if currency is None:
            raise NotFoundError("Currency not found")
        return currency

    async def update(self, farm_id: int, currency_id: int, data: CurrencyUpdate) -> Currency:
        currency = await self.get(farm_id, currency_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(currency, key, value)
        await self.db.commit()
        await self.db.refresh(currency)
        return currency

    async def archive(self, farm_id: int, currency_id: int) -> None:
        currency = await self.get(farm_id, currency_id)
        currency.archived_at = datetime.now(UTC)
        await self.db.commit()

    async def resolve_or_default(self, farm_id: int, currency_id: int | None) -> int:
        """Validate a chosen currency belongs to the farm and is active, or fall
        back to the currency matching the farm's preferred code when none is given."""
        if currency_id is not None:
            currency = await self.get(farm_id, currency_id)
            if currency.archived_at is not None:
                raise ValidationError("Currency is archived")
            return currency.id
        return await self._default_currency_id(farm_id)

    async def _default_currency_id(self, farm_id: int) -> int:
        farm = await self.db.get(Farm, farm_id)
        if farm is None:
            raise NotFoundError("Farm not found")
        stmt = select(Currency).where(
            Currency.farm_id == farm_id, Currency.code == farm.default_currency
        )
        default = (await self.db.execute(stmt)).scalar_one_or_none()
        if default is None:
            raise ValidationError("Farm has no currency matching its default code; create it first")
        return default.id

    async def list_currencies(
        self,
        *,
        farm_id: int,
        filters: CurrencyFilters,
        search: str | None,
        sort: str | None,
        page: PageParams,
    ) -> tuple[list[Currency], int]:
        stmt = select(Currency).where(Currency.farm_id == farm_id)
        if filters.archived is True:
            stmt = stmt.where(Currency.archived_at.is_not(None))
        elif filters.archived is False:
            stmt = stmt.where(Currency.archived_at.is_(None))
        stmt = apply_date_range(stmt, Currency.created_at, filters.date_from, filters.date_to)
        stmt = apply_search(stmt, search, SEARCH_COLUMNS)
        stmt = apply_sort(stmt, sort, SORT_ALLOWED)
        if sort is None:
            stmt = stmt.order_by(Currency.code.asc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.offset(page.offset).limit(page.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total
