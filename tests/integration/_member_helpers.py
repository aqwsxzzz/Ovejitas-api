from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.farm_member.models import FarmMember, FarmRole
from tests.conftest import AuthedUser

MEMBERS = "/api/v1/farms/{farm_id}/members"


async def add_member(db: AsyncSession, *, user_id: int, farm_id: int, role: FarmRole) -> int:
    """Insert a FarmMember directly and return its generated id."""
    member = FarmMember(user_id=user_id, farm_id=farm_id, role=role)
    db.add(member)
    await db.commit()
    return member.id


async def owner_member_id(db: AsyncSession, user: AuthedUser) -> int:
    """Return the FarmMember row id for a registered user's own farm membership."""
    stmt = select(FarmMember.id).where(
        FarmMember.user_id == user.user_id,
        FarmMember.farm_id == user.farm_id,
    )
    return (await db.execute(stmt)).scalar_one()
