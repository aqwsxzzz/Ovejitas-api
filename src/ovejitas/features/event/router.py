from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from ovejitas.core.deps import DBSession
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.asset.deps import AssetDep
from ovejitas.features.auth.deps import CurrentUser
from ovejitas.features.event.schemas import (
    EventCreate,
    EventFilters,
    EventRead,
    EventUpdate,
    InventoryBalance,
)
from ovejitas.features.event.service import EventService


def get_event_service(db: DBSession) -> EventService:
    return EventService(db)


EventSvc = Annotated[EventService, Depends(get_event_service)]

router = APIRouter(
    prefix="/farms/{farm_id}/assets/{asset_id}/events",
    tags=["events"],
)


@router.get(
    "",
    response_model=Page[EventRead],
    summary="List events for an asset",
)
async def list_events(
    asset: AssetDep,
    svc: EventSvc,
    page: Annotated[PageParams, Depends()],
    filters: Annotated[EventFilters, Depends()],
    q: Annotated[str | None, Query(description="Search notes")] = None,
    sort: Annotated[str | None, Query(description="e.g. -occurred_at")] = None,
) -> Page[EventRead]:
    rows, total = await svc.list_events(
        asset=asset, filters=filters, search=q, sort=sort, page=page
    )
    return Page.build([EventRead.model_validate(r) for r in rows], total, page)


@router.post(
    "",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an event",
    description=(
        "Body is a discriminated union on `type`. "
        "Reproductive events require `kind=animal` + `individual_id`. "
        "Individuals require `mode=individual` and must belong to this asset. "
        "Categories must match the event type."
    ),
)
async def create_event(
    asset: AssetDep,
    data: EventCreate,
    svc: EventSvc,
    current_user: CurrentUser,
) -> EventRead:
    return EventRead.model_validate(await svc.create(asset, current_user.id, data))


@router.get(
    "/balance",
    response_model=InventoryBalance,
    summary="Current on-hand inventory for a material asset",
    description=(
        "Returns the derived on-hand balance per (asset, unit), computed from "
        "INVENTORY events: sum of increments minus decrements since the most "
        "recent reset. Only meaningful for assets with kind=material."
    ),
)
async def asset_inventory_balance(
    asset: AssetDep,
    svc: EventSvc,
) -> InventoryBalance:
    return await svc.inventory_balance(asset)


@router.get(
    "/{event_id}",
    response_model=EventRead,
    summary="Get one event",
)
async def get_event(
    asset: AssetDep,
    event_id: int,
    svc: EventSvc,
) -> EventRead:
    return EventRead.model_validate(await svc.get(asset.id, event_id))


@router.patch(
    "/{event_id}",
    response_model=EventRead,
    summary="Update an event",
    description="`type` is immutable. Guards still apply to `individual_id` / `category_id`.",
)
async def update_event(
    asset: AssetDep,
    event_id: int,
    data: EventUpdate,
    svc: EventSvc,
) -> EventRead:
    return EventRead.model_validate(await svc.update(asset, event_id, data))


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an event",
)
async def delete_event(
    asset: AssetDep,
    event_id: int,
    svc: EventSvc,
) -> None:
    await svc.delete(asset.id, event_id)
