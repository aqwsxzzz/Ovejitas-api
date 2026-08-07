from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ConflictError, NotFoundError
from ovejitas.core.filters import apply_date_range
from ovejitas.core.pagination import PageParams
from ovejitas.core.search import apply_search
from ovejitas.core.sorting import apply_sort
from ovejitas.features.event.models import Event
from ovejitas.features.pregnancy.derive import resolve_expected_due_at
from ovejitas.features.pregnancy.events import (
    emit_reproductive,
    reconcile_reproductive,
    reverse_reproductive,
)
from ovejitas.features.pregnancy.guards import (
    assert_pregnancy_projection,
    validate_individual,
    validate_sire,
)
from ovejitas.features.pregnancy.models import Pregnancy
from ovejitas.features.pregnancy.schemas import (
    PregnancyCreate,
    PregnancyFilters,
    PregnancyUpdate,
)

SEARCH_COLUMNS = [Pregnancy.notes]
SORT_ALLOWED = {
    "occurred_at": Pregnancy.occurred_at,
    "expected_due_at": Pregnancy.expected_due_at,
    "created_at": Pregnancy.created_at,
    "updated_at": Pregnancy.updated_at,
}


class PregnancyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, farm_id: int, user_id: int, data: PregnancyCreate
    ) -> tuple[Pregnancy, bool]:
        """Returns (record, created). ``created`` is False on idempotency-key replay."""
        if data.idempotency_key is not None:
            existing = await self._by_idempotency_key(farm_id, data.idempotency_key)
            if existing is not None:
                return existing, False
        individual = await validate_individual(self.db, farm_id, data.individual_id)
        await validate_sire(self.db, farm_id, data.individual_id, data.sire_individual_id)
        fields = data.model_dump()
        fields["expected_due_at"] = await resolve_expected_due_at(
            self.db, individual=individual, data=data
        )
        try:
            pregnancy = Pregnancy(farm_id=farm_id, created_by=user_id, **fields)
            event = await emit_reproductive(
                self.db, individual=individual, pregnancy=pregnancy, created_by=user_id
            )
            pregnancy.reproductive_event_id = event.id
            self.db.add(pregnancy)
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            replay = await self._by_idempotency_key(farm_id, data.idempotency_key)
            if replay is not None:
                return replay, False
            raise ConflictError("Pregnancy conflict") from exc
        except Exception:
            await self.db.rollback()
            raise
        await self.db.refresh(pregnancy)
        return pregnancy, True

    async def get(self, farm_id: int, pregnancy_id: int) -> Pregnancy:
        stmt = select(Pregnancy).where(
            Pregnancy.id == pregnancy_id,
            Pregnancy.farm_id == farm_id,
        )
        row = (await self.db.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise NotFoundError("Pregnancy not found")
        return row

    async def update(self, farm_id: int, pregnancy_id: int, data: PregnancyUpdate) -> Pregnancy:
        pregnancy = await self.get(farm_id, pregnancy_id)
        updates = data.model_dump(exclude_unset=True)
        assert_pregnancy_projection(
            updates.get("is_pregnant", pregnancy.is_pregnant),
            updates.get("offspring_count", pregnancy.offspring_count),
            updates.get("expected_due_at", pregnancy.expected_due_at),
        )
        if "sire_individual_id" in updates:
            await validate_sire(
                self.db, farm_id, pregnancy.individual_id, updates["sire_individual_id"]
            )
        try:
            event = await self.db.get(Event, pregnancy.reproductive_event_id)
            if event is None:
                raise NotFoundError("Paired reproductive event missing")
            for key, value in updates.items():
                setattr(pregnancy, key, value)
            await reconcile_reproductive(self.db, event=event, pregnancy=pregnancy)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        await self.db.refresh(pregnancy)
        return pregnancy

    async def delete(self, farm_id: int, pregnancy_id: int) -> None:
        pregnancy = await self.get(farm_id, pregnancy_id)
        event = await self.db.get(Event, pregnancy.reproductive_event_id)
        try:
            await self.db.delete(pregnancy)
            await self.db.flush()
            if event is not None:
                await reverse_reproductive(self.db, event=event)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def list_pregnancies(
        self,
        *,
        farm_id: int,
        filters: PregnancyFilters,
        search: str | None,
        sort: str | None,
        page: PageParams,
    ) -> tuple[list[Pregnancy], int]:
        stmt = select(Pregnancy).where(Pregnancy.farm_id == farm_id)
        if filters.individual_id is not None:
            stmt = stmt.where(Pregnancy.individual_id == filters.individual_id)
        if filters.sire_individual_id is not None:
            stmt = stmt.where(Pregnancy.sire_individual_id == filters.sire_individual_id)
        if filters.is_pregnant is not None:
            stmt = stmt.where(Pregnancy.is_pregnant.is_(filters.is_pregnant))
        stmt = apply_date_range(stmt, Pregnancy.occurred_at, filters.date_from, filters.date_to)
        stmt = apply_search(stmt, search, SEARCH_COLUMNS)
        stmt = apply_sort(stmt, sort, SORT_ALLOWED)
        if sort is None:
            stmt = stmt.order_by(Pregnancy.occurred_at.desc(), Pregnancy.id.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(page.offset).limit(page.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total

    async def _by_idempotency_key(self, farm_id: int, key: str | None) -> Pregnancy | None:
        if key is None:
            return None
        stmt = select(Pregnancy).where(
            Pregnancy.farm_id == farm_id,
            Pregnancy.idempotency_key == key,
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()
