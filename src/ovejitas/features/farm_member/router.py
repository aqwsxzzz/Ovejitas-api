from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status

from ovejitas.core.deps import DBSession
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.farm_member.deps import require_farm_member, require_farm_role
from ovejitas.features.farm_member.models import FarmMember, FarmRole
from ovejitas.features.farm_member.schemas import (
    MemberFilters,
    MemberRead,
    MemberRoleUpdate,
)
from ovejitas.features.farm_member.service import FarmMemberService


def get_member_service(db: DBSession) -> FarmMemberService:
    return FarmMemberService(db)


MemberSvc = Annotated[FarmMemberService, Depends(get_member_service)]
ViewMembers = Annotated[FarmMember, Depends(require_farm_member)]
ManageMembers = Annotated[FarmMember, Depends(require_farm_role(FarmRole.OWNER, FarmRole.ADMIN))]

# Documented failure modes for owner/admin-gated management routes.
_MANAGE_ERRORS: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {"description": "Missing or invalid access token"},
    status.HTTP_403_FORBIDDEN: {"description": "Not an owner or admin, or cannot manage an owner"},
    status.HTTP_404_NOT_FOUND: {"description": "Member not found"},
}

router = APIRouter(tags=["members"])


@router.get(
    "/farms/{farm_id}/members",
    response_model=Page[MemberRead],
    summary="List farm members",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Missing or invalid access token"},
        status.HTTP_403_FORBIDDEN: {"description": "Not a member of this farm"},
    },
)
async def list_members(
    farm_id: int,
    svc: MemberSvc,
    _membership: ViewMembers,
    page: Annotated[PageParams, Depends()],
    filters: Annotated[MemberFilters, Depends()],
    sort: Annotated[str | None, Query(description="e.g. -created_at,role")] = None,
) -> Page[MemberRead]:
    rows, total = await svc.list(farm_id=farm_id, filters=filters, sort=sort, page=page)
    return Page.build([MemberRead.model_validate(r) for r in rows], total, page)


@router.patch(
    "/farms/{farm_id}/members/{member_id}",
    response_model=MemberRead,
    summary="Change a member's role (owner/admin only)",
    responses={
        **_MANAGE_ERRORS,
        status.HTTP_409_CONFLICT: {"description": "Cannot demote the last owner"},
    },
)
async def update_member_role(
    farm_id: int,
    member_id: int,
    data: MemberRoleUpdate,
    svc: MemberSvc,
    membership: ManageMembers,
) -> FarmMember:
    return await svc.change_role(farm_id, member_id, data.role, membership)


@router.delete(
    "/farms/{farm_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from the farm (owner/admin only)",
    responses={
        **_MANAGE_ERRORS,
        status.HTTP_409_CONFLICT: {"description": "Cannot remove the last owner"},
    },
)
async def remove_member(
    farm_id: int,
    member_id: int,
    svc: MemberSvc,
    membership: ManageMembers,
) -> None:
    await svc.remove(farm_id, member_id, membership)
