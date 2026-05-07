from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from ovejitas.core.deps import DBSession
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.event_category.schemas import (
    EventCategoryCreate,
    EventCategoryFilters,
    EventCategoryRead,
    EventCategoryUpdate,
)
from ovejitas.features.event_category.service import EventCategoryService
from ovejitas.features.farm_member.deps import FarmMembership


def get_event_category_service(db: DBSession) -> EventCategoryService:
    return EventCategoryService(db)


EventCategorySvc = Annotated[EventCategoryService, Depends(get_event_category_service)]

router = APIRouter(prefix="/farms/{farm_id}/event-categories", tags=["event-categories"])


@router.get(
    "",
    response_model=Page[EventCategoryRead],
    summary="List event categories in a farm",
)
async def list_event_categories(
    farm_id: int,
    svc: EventCategorySvc,
    _membership: FarmMembership,
    page: Annotated[PageParams, Depends()],
    filters: Annotated[EventCategoryFilters, Depends()],
    q: Annotated[str | None, Query(description="Search across name")] = None,
    sort: Annotated[str | None, Query(description="e.g. -created_at,name")] = None,
) -> Page[EventCategoryRead]:
    rows, total = await svc.list_categories(
        farm_id=farm_id, filters=filters, search=q, sort=sort, page=page
    )
    return Page.build([EventCategoryRead.model_validate(r) for r in rows], total, page)


@router.post(
    "",
    response_model=EventCategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an event category",
    description="`type` is immutable after creation. Uniqueness enforced on (farm, type, name).",
)
async def create_event_category(
    farm_id: int,
    data: EventCategoryCreate,
    svc: EventCategorySvc,
    _membership: FarmMembership,
) -> EventCategoryRead:
    return EventCategoryRead.model_validate(await svc.create(farm_id, data))


@router.get(
    "/{category_id}",
    response_model=EventCategoryRead,
    summary="Get one event category",
)
async def get_event_category(
    farm_id: int,
    category_id: int,
    svc: EventCategorySvc,
    _membership: FarmMembership,
) -> EventCategoryRead:
    return EventCategoryRead.model_validate(await svc.get(farm_id, category_id))


@router.patch(
    "/{category_id}",
    response_model=EventCategoryRead,
    summary="Update an event category",
    description="Set `archived_at` to archive; set to null to unarchive. `type` cannot change.",
)
async def update_event_category(
    farm_id: int,
    category_id: int,
    data: EventCategoryUpdate,
    svc: EventCategorySvc,
    _membership: FarmMembership,
) -> EventCategoryRead:
    return EventCategoryRead.model_validate(await svc.update(farm_id, category_id, data))


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an event category",
    description="Events referencing this category have their `category_id` set to null.",
)
async def delete_event_category(
    farm_id: int,
    category_id: int,
    svc: EventCategorySvc,
    _membership: FarmMembership,
) -> None:
    await svc.delete(farm_id, category_id)
