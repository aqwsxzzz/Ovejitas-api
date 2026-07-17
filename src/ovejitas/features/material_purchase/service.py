from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ConflictError, NotFoundError
from ovejitas.core.filters import apply_date_range
from ovejitas.core.pagination import PageParams
from ovejitas.core.search import apply_search
from ovejitas.core.sorting import apply_sort
from ovejitas.features.asset.models import Asset
from ovejitas.features.currency.service import CurrencyService
from ovejitas.features.material_purchase.events import emit_pair, reconcile_pair, reverse_pair
from ovejitas.features.material_purchase.guards import (
    validate_material_asset,
    validate_purchase_unit,
)
from ovejitas.features.material_purchase.models import MaterialPurchase
from ovejitas.features.material_purchase.schemas import (
    MaterialPurchaseCreate,
    MaterialPurchaseFilters,
    MaterialPurchaseUpdate,
)

SEARCH_COLUMNS = [MaterialPurchase.notes, MaterialPurchase.supplier]
SORT_ALLOWED = {
    "occurred_at": MaterialPurchase.occurred_at,
    "quantity": MaterialPurchase.quantity,
    "amount": MaterialPurchase.amount,
    "created_at": MaterialPurchase.created_at,
    "updated_at": MaterialPurchase.updated_at,
}


class MaterialPurchaseService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, farm_id: int, user_id: int, data: MaterialPurchaseCreate
    ) -> tuple[MaterialPurchase, bool]:
        """Returns (record, created). ``created`` is False on idempotency-key replay."""
        existing = await self._by_idempotency_key(farm_id, data.idempotency_key)
        if existing is not None:
            return existing, False
        material = await self._validate_create(farm_id, data)
        currency_id = await CurrencyService(self.db).resolve_or_default(farm_id, data.currency_id)
        try:
            inventory_event_id, expense_event_id = await emit_pair(
                self.db, material=material, data=data, currency_id=currency_id, user_id=user_id
            )
            purchase = MaterialPurchase(
                farm_id=farm_id,
                inventory_event_id=inventory_event_id,
                expense_event_id=expense_event_id,
                currency_id=currency_id,
                created_by=user_id,
                **data.model_dump(exclude={"currency_id"}),
            )
            self.db.add(purchase)
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            replay = await self._by_idempotency_key(farm_id, data.idempotency_key)
            if replay is not None:
                return replay, False
            raise ConflictError("Material purchase conflict") from exc
        except Exception:
            await self.db.rollback()
            raise
        await self.db.refresh(purchase)
        return purchase, True

    async def get(self, farm_id: int, purchase_id: int) -> MaterialPurchase:
        stmt = select(MaterialPurchase).where(
            MaterialPurchase.id == purchase_id,
            MaterialPurchase.farm_id == farm_id,
        )
        row = (await self.db.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise NotFoundError("Material purchase not found")
        return row

    async def update(
        self, farm_id: int, purchase_id: int, data: MaterialPurchaseUpdate
    ) -> MaterialPurchase:
        purchase = await self.get(farm_id, purchase_id)
        updates = data.model_dump(exclude_unset=True)
        try:
            if "unit" in updates:
                await validate_purchase_unit(self.db, purchase.material_asset_id, updates["unit"])
            await reconcile_pair(self.db, purchase=purchase, updates=updates)
            for key, value in updates.items():
                setattr(purchase, key, value)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        await self.db.refresh(purchase)
        return purchase

    async def delete(self, farm_id: int, purchase_id: int) -> None:
        purchase = await self.get(farm_id, purchase_id)
        material_asset_id = purchase.material_asset_id
        inventory_event_id = purchase.inventory_event_id
        expense_event_id = purchase.expense_event_id
        try:
            await self.db.delete(purchase)
            await self.db.flush()
            await reverse_pair(
                self.db,
                material_asset_id=material_asset_id,
                inventory_event_id=inventory_event_id,
                expense_event_id=expense_event_id,
            )
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def list_purchases(
        self,
        *,
        farm_id: int,
        filters: MaterialPurchaseFilters,
        search: str | None,
        sort: str | None,
        page: PageParams,
    ) -> tuple[list[MaterialPurchase], int]:
        stmt = select(MaterialPurchase).where(MaterialPurchase.farm_id == farm_id)
        if filters.material_asset_id is not None:
            stmt = stmt.where(MaterialPurchase.material_asset_id == filters.material_asset_id)
        stmt = apply_date_range(
            stmt, MaterialPurchase.occurred_at, filters.date_from, filters.date_to
        )
        stmt = apply_search(stmt, search, SEARCH_COLUMNS)
        stmt = apply_sort(stmt, sort, SORT_ALLOWED)
        if sort is None:
            stmt = stmt.order_by(MaterialPurchase.occurred_at.desc(), MaterialPurchase.id.desc())
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(page.offset).limit(page.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total

    async def _validate_create(self, farm_id: int, data: MaterialPurchaseCreate) -> Asset:
        material = await validate_material_asset(self.db, farm_id, data.material_asset_id)
        await validate_purchase_unit(self.db, material.id, data.unit)
        return material

    async def _by_idempotency_key(self, farm_id: int, key: str | None) -> MaterialPurchase | None:
        if key is None:
            return None
        stmt = select(MaterialPurchase).where(
            MaterialPurchase.farm_id == farm_id,
            MaterialPurchase.idempotency_key == key,
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()
