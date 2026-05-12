from typing import Annotated

from fastapi import Depends
from sqlalchemy import select

from ovejitas.core.deps import DBSession
from ovejitas.core.errors import ForbiddenError
from ovejitas.features.auth.deps import CurrentUser
from ovejitas.features.farm_member.models import FarmMember


async def require_farm_member(
    farm_id: int,
    current_user: CurrentUser,
    db: DBSession,
) -> FarmMember:
    stmt = select(FarmMember).where(
        FarmMember.user_id == current_user.id,
        FarmMember.farm_id == farm_id,
    )
    membership = (await db.execute(stmt)).scalar_one_or_none()
    if membership is None:
        raise ForbiddenError("Not a member of this farm")
    return membership


FarmMembership = Annotated[FarmMember, Depends(require_farm_member)]
