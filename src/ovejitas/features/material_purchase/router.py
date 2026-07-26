from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from ovejitas.core.deps import DBSession
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.farm.deps import farm_local
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.material_purchase.schemas import (
    MaterialPurchaseCreate,
    MaterialPurchaseFilters,
    MaterialPurchaseRead,
    MaterialPurchaseUpdate,
)
from ovejitas.features.material_purchase.service import MaterialPurchaseService


def get_material_purchase_service(db: DBSession) -> MaterialPurchaseService:
    return MaterialPurchaseService(db)


MaterialPurchaseSvc = Annotated[MaterialPurchaseService, Depends(get_material_purchase_service)]

router = APIRouter(
    prefix="/farms/{farm_id}/material-purchases",
    tags=["material-purchases"],
)


@router.get(
    "",
    response_model=Page[MaterialPurchaseRead],
    summary="List material purchases in a farm",
)
async def list_material_purchases(
    farm_id: int,
    svc: MaterialPurchaseSvc,
    _membership: FarmMembership,
    page: Annotated[PageParams, Depends()],
    filters: Annotated[MaterialPurchaseFilters, Depends(farm_local(MaterialPurchaseFilters))],
    q: Annotated[str | None, Query(description="Search notes and supplier")] = None,
    sort: Annotated[str | None, Query(description="e.g. -occurred_at,amount")] = None,
) -> Page[MaterialPurchaseRead]:
    rows, total = await svc.list_purchases(
        farm_id=farm_id, filters=filters, search=q, sort=sort, page=page
    )
    return Page.build([MaterialPurchaseRead.model_validate(r) for r in rows], total, page)


@router.post(
    "",
    response_model=MaterialPurchaseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a material purchase",
    description=(
        "Atomically records the purchase, increments the material's stock, and "
        "books an expense for the amount paid — via a paired INVENTORY and EXPENSE "
        "event. The purchased `unit` must match how the material is already "
        "tracked (any unit is allowed for a material with no inventory history). "
        "Replaying an `idempotency_key` returns the original record with status 200."
    ),
)
async def create_material_purchase(
    farm_id: int,
    data: MaterialPurchaseCreate,
    svc: MaterialPurchaseSvc,
    membership: FarmMembership,
    response: Response,
) -> MaterialPurchaseRead:
    purchase, created = await svc.create(farm_id, membership.user_id, data)
    if not created:
        response.status_code = status.HTTP_200_OK
    return MaterialPurchaseRead.model_validate(purchase)


@router.get(
    "/{purchase_id}",
    response_model=MaterialPurchaseRead,
    summary="Get one material purchase",
)
async def get_material_purchase(
    farm_id: int,
    purchase_id: int,
    svc: MaterialPurchaseSvc,
    _membership: FarmMembership,
) -> MaterialPurchaseRead:
    return MaterialPurchaseRead.model_validate(await svc.get(farm_id, purchase_id))


@router.patch(
    "/{purchase_id}",
    response_model=MaterialPurchaseRead,
    summary="Update a material purchase",
    description=(
        "`material_asset_id` is immutable. Changing `quantity`/`unit`/`occurred_at` "
        "reconciles the inventory event; `amount`/`occurred_at` reconciles the "
        "expense. An edit that would drive stock negative is rejected with 409."
    ),
)
async def update_material_purchase(
    farm_id: int,
    purchase_id: int,
    data: MaterialPurchaseUpdate,
    svc: MaterialPurchaseSvc,
    _membership: FarmMembership,
) -> MaterialPurchaseRead:
    return MaterialPurchaseRead.model_validate(await svc.update(farm_id, purchase_id, data))


@router.delete(
    "/{purchase_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a material purchase",
    description=(
        "Hard-deletes the record and reverses both the stock increment and the "
        "expense. Rejected with 409 if reversing the stock would go negative."
    ),
)
async def delete_material_purchase(
    farm_id: int,
    purchase_id: int,
    svc: MaterialPurchaseSvc,
    _membership: FarmMembership,
) -> None:
    await svc.delete(farm_id, purchase_id)
