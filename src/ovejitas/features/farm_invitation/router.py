from typing import Annotated, Any

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

# Documented failure modes (the service raises these AppError subclasses at runtime).
_MANAGE_ERRORS: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {"description": "Missing or invalid access token"},
    status.HTTP_403_FORBIDDEN: {"description": "Not an owner or admin of this farm"},
}
_TOKEN_ERRORS: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {"description": "Invitation not found or revoked"},
    status.HTTP_409_CONFLICT: {"description": "Invitation already accepted"},
    status.HTTP_410_GONE: {"description": "Invitation expired"},
}

router = APIRouter(tags=["invitations"])


@router.post(
    "/farms/{farm_id}/invitations",
    response_model=InvitationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an invitation link (owner/admin only)",
    responses={
        **_MANAGE_ERRORS,
        status.HTTP_409_CONFLICT: {
            "description": "Email is already a member, or a pending invite already exists"
        },
    },
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
    responses={**_MANAGE_ERRORS},
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
    responses={
        **_MANAGE_ERRORS,
        status.HTTP_404_NOT_FOUND: {"description": "Invitation not found"},
        status.HTTP_409_CONFLICT: {"description": "Only pending invitations can be revoked"},
    },
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
    responses={**_TOKEN_ERRORS},
)
async def resolve_invitation(token: str, svc: InvitationSvc) -> InvitationResolve:
    return await svc.resolve(token)


@router.post(
    "/invitations/{token}/accept",
    response_model=TokenPair,
    summary="Accept an invitation; joins the farm and returns tokens (public)",
    responses={
        **_TOKEN_ERRORS,
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Incorrect password for the existing account"
        },
        status.HTTP_409_CONFLICT: {
            "description": "Invitation already accepted, or user is already a member"
        },
    },
)
async def accept_invitation(token: str, data: AcceptInvitation, svc: InvitationSvc) -> TokenPair:
    return await svc.accept(token, data)
