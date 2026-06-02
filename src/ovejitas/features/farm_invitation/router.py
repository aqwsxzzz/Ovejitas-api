from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from ovejitas.core.deps import DBSession
from ovejitas.core.pagination import Page, PageParams
from ovejitas.features.auth.schemas import TokenPair
from ovejitas.features.farm_invitation.schemas import (
    AcceptInvitation,
    InvitationCreate,
    InvitationCreateResponse,
    InvitationFilters,
    InvitationRead,
    InvitationResolve,
)
from ovejitas.features.farm_invitation.service import InvitationService
from ovejitas.features.farm_member.deps import require_farm_role
from ovejitas.features.farm_member.models import FarmMember, FarmRole


def get_invitation_service(db: DBSession) -> InvitationService:
    return InvitationService(db)


InvitationSvc = Annotated[InvitationService, Depends(get_invitation_service)]
ManageInvites = Annotated[FarmMember, Depends(require_farm_role(FarmRole.OWNER, FarmRole.ADMIN))]

router = APIRouter(tags=["invitations"])


@router.post(
    "/farms/{farm_id}/invitations",
    response_model=InvitationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an invitation link (owner/admin only)",
)
async def create_invitation(
    farm_id: int,
    data: InvitationCreate,
    svc: InvitationSvc,
    membership: ManageInvites,
) -> InvitationCreateResponse:
    invite, token = await svc.create(farm_id, membership.user_id, data)
    return InvitationCreateResponse(invitation=InvitationRead.model_validate(invite), token=token)


@router.get(
    "/farms/{farm_id}/invitations",
    response_model=Page[InvitationRead],
    summary="List invitations for a farm (owner/admin only)",
)
async def list_invitations(
    farm_id: int,
    svc: InvitationSvc,
    _membership: ManageInvites,
    page: Annotated[PageParams, Depends()],
    filters: Annotated[InvitationFilters, Depends()],
    sort: Annotated[str | None, Query(description="e.g. -created_at,email")] = None,
) -> Page[InvitationRead]:
    rows, total = await svc.list(farm_id=farm_id, filters=filters, sort=sort, page=page)
    return Page.build([InvitationRead.model_validate(r) for r in rows], total, page)


@router.post(
    "/farms/{farm_id}/invitations/{invitation_id}/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a pending invitation (owner/admin only)",
)
async def revoke_invitation(
    farm_id: int,
    invitation_id: int,
    svc: InvitationSvc,
    _membership: ManageInvites,
) -> None:
    await svc.revoke(farm_id, invitation_id)


@router.get(
    "/invitations/{token}",
    response_model=InvitationResolve,
    summary="Resolve an invitation token (public)",
)
async def resolve_invitation(token: str, svc: InvitationSvc) -> InvitationResolve:
    return await svc.resolve(token)


@router.post(
    "/invitations/{token}/accept",
    response_model=TokenPair,
    summary="Accept an invitation; joins the farm and returns tokens (public)",
)
async def accept_invitation(token: str, data: AcceptInvitation, svc: InvitationSvc) -> TokenPair:
    return await svc.accept(token, data)
