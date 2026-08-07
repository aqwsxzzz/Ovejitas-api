from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from ovejitas.core.deps import DBSession
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.farm.deps import farm_local
from ovejitas.features.farm_member.deps import FarmMembership
from ovejitas.features.pregnancy.schemas import (
    PregnancyCreate,
    PregnancyFilters,
    PregnancyRead,
    PregnancyUpdate,
)
from ovejitas.features.pregnancy.service import PregnancyService


def get_pregnancy_service(db: DBSession) -> PregnancyService:
    return PregnancyService(db)


PregnancySvc = Annotated[PregnancyService, Depends(get_pregnancy_service)]

router = APIRouter(prefix="/farms/{farm_id}/pregnancies", tags=["pregnancies"])


@router.get(
    "",
    response_model=Page[PregnancyRead],
    summary="List pregnancy records in a farm",
)
async def list_pregnancies(
    farm_id: int,
    svc: PregnancySvc,
    _membership: FarmMembership,
    page: Annotated[PageParams, Depends()],
    filters: Annotated[PregnancyFilters, Depends(farm_local(PregnancyFilters))],
    q: Annotated[str | None, Query(description="Search notes")] = None,
    sort: Annotated[str | None, Query(description="e.g. -occurred_at,expected_due_at")] = None,
) -> Page[PregnancyRead]:
    rows, total = await svc.list_pregnancies(
        farm_id=farm_id, filters=filters, search=q, sort=sort, page=page
    )
    return Page.build([PregnancyRead.model_validate(r) for r in rows], total, page)


@router.post(
    "",
    response_model=PregnancyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a pregnancy / ultrasound check",
    description=(
        "Records a pregnancy check on one individual and emits a paired "
        "REPRODUCTIVE event on its timeline. A non-pregnant check must omit "
        "`offspring_count` and `expected_due_at`. Replaying an `idempotency_key` "
        "returns the original record with status 200.\n\n"
        "Omit `expected_due_at` on a positive check to have it derived as "
        "`(service_date or occurred_at) + asset.gestation_days`. A value you "
        "supply is always kept as given, and an asset with no `gestation_days` "
        "configured derives nothing rather than erroring. `sire_individual_id` "
        "must be a different individual in the same farm."
    ),
)
async def create_pregnancy(
    farm_id: int,
    data: PregnancyCreate,
    svc: PregnancySvc,
    membership: FarmMembership,
    response: Response,
) -> PregnancyRead:
    pregnancy, created = await svc.create(farm_id, membership.user_id, data)
    if not created:
        response.status_code = status.HTTP_200_OK
    return PregnancyRead.model_validate(pregnancy)


@router.get(
    "/{pregnancy_id}",
    response_model=PregnancyRead,
    summary="Get one pregnancy record",
)
async def get_pregnancy(
    farm_id: int,
    pregnancy_id: int,
    svc: PregnancySvc,
    _membership: FarmMembership,
) -> PregnancyRead:
    return PregnancyRead.model_validate(await svc.get(farm_id, pregnancy_id))


@router.patch(
    "/{pregnancy_id}",
    response_model=PregnancyRead,
    summary="Update a pregnancy record",
    description=(
        "`individual_id` is immutable. Changes reconcile the paired reproductive "
        "event. Clearing `is_pregnant` requires also clearing `offspring_count` "
        "and `expected_due_at`. `expected_due_at` is never re-derived here: "
        "editing `service_date` leaves an already-stored due date alone."
    ),
)
async def update_pregnancy(
    farm_id: int,
    pregnancy_id: int,
    data: PregnancyUpdate,
    svc: PregnancySvc,
    _membership: FarmMembership,
) -> PregnancyRead:
    return PregnancyRead.model_validate(await svc.update(farm_id, pregnancy_id, data))


@router.delete(
    "/{pregnancy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a pregnancy record",
    description="Hard-deletes the record and reverses its reproductive event.",
)
async def delete_pregnancy(
    farm_id: int,
    pregnancy_id: int,
    svc: PregnancySvc,
    _membership: FarmMembership,
) -> None:
    await svc.delete(farm_id, pregnancy_id)
