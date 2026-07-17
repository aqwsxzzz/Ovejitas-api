from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from ovejitas.core.deps import DBSession
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.currency.schemas import (
    CurrencyCreate,
    CurrencyFilters,
    CurrencyRead,
    CurrencyUpdate,
)
from ovejitas.features.currency.service import CurrencyService
from ovejitas.features.farm_member.deps import FarmMembership


def get_currency_service(db: DBSession) -> CurrencyService:
    return CurrencyService(db)


CurrencySvc = Annotated[CurrencyService, Depends(get_currency_service)]

router = APIRouter(prefix="/farms/{farm_id}/currencies", tags=["currencies"])


@router.get(
    "",
    response_model=Page[CurrencyRead],
    summary="List currencies in a farm",
)
async def list_currencies(
    farm_id: int,
    svc: CurrencySvc,
    _membership: FarmMembership,
    page: Annotated[PageParams, Depends()],
    filters: Annotated[CurrencyFilters, Depends()],
    q: Annotated[str | None, Query(description="Search across code and name")] = None,
    sort: Annotated[str | None, Query(description="e.g. -created_at,code")] = None,
) -> Page[CurrencyRead]:
    rows, total = await svc.list_currencies(
        farm_id=farm_id, filters=filters, search=q, sort=sort, page=page
    )
    return Page.build([CurrencyRead.model_validate(r) for r in rows], total, page)


@router.post(
    "",
    response_model=CurrencyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Enable a currency for a farm",
    description="`code` is a supported ISO 4217 code and is immutable after creation. "
    "Uniqueness enforced on (farm, code).",
)
async def create_currency(
    farm_id: int,
    data: CurrencyCreate,
    svc: CurrencySvc,
    _membership: FarmMembership,
) -> CurrencyRead:
    return CurrencyRead.model_validate(await svc.create(farm_id, data))


@router.get(
    "/{currency_id}",
    response_model=CurrencyRead,
    summary="Get one currency",
)
async def get_currency(
    farm_id: int,
    currency_id: int,
    svc: CurrencySvc,
    _membership: FarmMembership,
) -> CurrencyRead:
    return CurrencyRead.model_validate(await svc.get(farm_id, currency_id))


@router.patch(
    "/{currency_id}",
    response_model=CurrencyRead,
    summary="Update a currency",
    description="Only `name`/`symbol` are editable; `code` is frozen. "
    "Set `archived_at` to archive, or null to unarchive.",
)
async def update_currency(
    farm_id: int,
    currency_id: int,
    data: CurrencyUpdate,
    svc: CurrencySvc,
    _membership: FarmMembership,
) -> CurrencyRead:
    return CurrencyRead.model_validate(await svc.update(farm_id, currency_id, data))


@router.delete(
    "/{currency_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive a currency",
    description="Currencies are never hard-deleted while ledger events reference them; "
    "this archives the currency (hidden from pickers, history intact).",
)
async def archive_currency(
    farm_id: int,
    currency_id: int,
    svc: CurrencySvc,
    _membership: FarmMembership,
) -> None:
    await svc.archive(farm_id, currency_id)
