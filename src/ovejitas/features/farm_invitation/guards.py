from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ConflictError
from ovejitas.features.farm_invitation.models import FarmInvitation, InvitationStatus
from ovejitas.features.farm_member.models import FarmMember


async def is_member(db: AsyncSession, farm_id: int, user_id: int) -> bool:
    stmt = select(FarmMember.id).where(
        FarmMember.farm_id == farm_id,
        FarmMember.user_id == user_id,
    )
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def ensure_no_pending_invite(db: AsyncSession, farm_id: int, email: str) -> None:
    stmt = select(FarmInvitation.id).where(
        FarmInvitation.farm_id == farm_id,
        FarmInvitation.email == email,
        FarmInvitation.status == InvitationStatus.PENDING,
    )
    if (await db.execute(stmt)).scalar_one_or_none() is not None:
        raise ConflictError("A pending invitation already exists for this email")
