import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import (
    ConflictError,
    GoneError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from ovejitas.core.pagination import PageParams
from ovejitas.core.security import verify_password
from ovejitas.core.sorting import apply_sort
from ovejitas.features.auth.schemas import TokenPair
from ovejitas.features.auth.service import AuthService, issue_token_pair
from ovejitas.features.farm.models import Farm
from ovejitas.features.farm_invitation.guards import ensure_no_pending_invite, is_member
from ovejitas.features.farm_invitation.models import FarmInvitation, InvitationStatus
from ovejitas.features.farm_invitation.schemas import (
    AcceptInvitation,
    InvitationCreate,
    InvitationFilters,
    InvitationResolve,
)
from ovejitas.features.farm_member.models import FarmMember
from ovejitas.features.user.models import User

INVITE_TTL_DAYS = 7
SORT_ALLOWED = {
    "created_at": FarmInvitation.created_at,
    "expires_at": FarmInvitation.expires_at,
    "email": FarmInvitation.email,
}


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class InvitationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.auth = AuthService(db)

    async def create(
        self, farm_id: int, invited_by: int, data: InvitationCreate
    ) -> tuple[FarmInvitation, str]:
        existing = await self.auth.find_by_email(data.email)
        if existing is not None and await is_member(self.db, farm_id, existing.id):
            raise ConflictError("User is already a member of this farm")
        await ensure_no_pending_invite(self.db, farm_id, data.email)

        token = secrets.token_urlsafe(32)
        invite = FarmInvitation(
            farm_id=farm_id,
            email=data.email,
            token_hash=_hash_token(token),
            role=data.role,
            status=InvitationStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(days=INVITE_TTL_DAYS),
            invited_by=invited_by,
        )
        self.db.add(invite)
        await self.db.commit()
        await self.db.refresh(invite)
        return invite, token

    async def list(
        self, farm_id: int, filters: InvitationFilters, sort: str | None, page: PageParams
    ) -> tuple[list[FarmInvitation], int]:
        stmt = select(FarmInvitation).where(FarmInvitation.farm_id == farm_id)
        if filters.status is not None:
            stmt = stmt.where(FarmInvitation.status == filters.status)
        stmt = apply_sort(stmt, sort, SORT_ALLOWED)
        if sort is None:
            stmt = stmt.order_by(FarmInvitation.created_at.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.offset(page.offset).limit(page.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total

    async def revoke(self, farm_id: int, invitation_id: int) -> None:
        invite = await self._get(farm_id, invitation_id)
        if invite.status is not InvitationStatus.PENDING:
            raise ConflictError("Only pending invitations can be revoked")
        invite.status = InvitationStatus.REVOKED
        await self.db.commit()

    async def resolve(self, token: str) -> InvitationResolve:
        invite = await self._valid_pending(token)
        farm = await self.db.get(Farm, invite.farm_id)
        if farm is None:
            raise NotFoundError("Invitation not found")
        existing = await self.auth.find_by_email(invite.email)
        return InvitationResolve(
            farm_id=invite.farm_id,
            farm_name=farm.name,
            role=invite.role,
            email=invite.email,
            requires_registration=existing is None,
        )

    async def accept(self, token: str, data: AcceptInvitation) -> TokenPair:
        invite = await self._valid_pending(token)
        user = await self.auth.find_by_email(invite.email)
        if user is None:
            user = await self._register_invitee(invite, data)
        else:
            self._verify_existing(user, data)

        if await is_member(self.db, invite.farm_id, user.id):
            raise ConflictError("Already a member of this farm")
        self.db.add(FarmMember(user_id=user.id, farm_id=invite.farm_id, role=invite.role))
        invite.status = InvitationStatus.ACCEPTED
        await self.db.commit()
        return issue_token_pair(user)

    async def _register_invitee(self, invite: FarmInvitation, data: AcceptInvitation) -> User:
        if not data.name:
            raise ValidationError("name is required to create a new account")
        return await self.auth.create_user(
            email=invite.email, name=data.name, password=data.password
        )

    def _verify_existing(self, user: User, data: AcceptInvitation) -> None:
        if not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Incorrect password")

    async def _get(self, farm_id: int, invitation_id: int) -> FarmInvitation:
        stmt = select(FarmInvitation).where(
            FarmInvitation.id == invitation_id,
            FarmInvitation.farm_id == farm_id,
        )
        invite = (await self.db.execute(stmt)).scalar_one_or_none()
        if invite is None:
            raise NotFoundError("Invitation not found")
        return invite

    async def _valid_pending(self, token: str) -> FarmInvitation:
        stmt = select(FarmInvitation).where(FarmInvitation.token_hash == _hash_token(token))
        invite = (await self.db.execute(stmt)).scalar_one_or_none()
        if invite is None or invite.status is InvitationStatus.REVOKED:
            raise NotFoundError("Invitation not found")
        if invite.status is InvitationStatus.ACCEPTED:
            raise ConflictError("Invitation already accepted")
        if invite.expires_at < datetime.now(UTC):
            raise GoneError("Invitation expired")
        return invite
