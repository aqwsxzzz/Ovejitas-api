from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ovejitas.core.errors import ConflictError, ForbiddenError, NotFoundError
from ovejitas.core.pagination import PageParams
from ovejitas.core.sorting import apply_sort
from ovejitas.features.farm_member.models import FarmMember, FarmRole
from ovejitas.features.farm_member.schemas import MemberFilters

SORT_ALLOWED = {
    "created_at": FarmMember.created_at,
    "role": FarmMember.role,
}


class FarmMemberService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(
        self, farm_id: int, filters: MemberFilters, sort: str | None, page: PageParams
    ) -> tuple[list[FarmMember], int]:
        stmt = (
            select(FarmMember)
            .where(FarmMember.farm_id == farm_id)
            .options(selectinload(FarmMember.user))
        )
        if filters.role is not None:
            stmt = stmt.where(FarmMember.role == filters.role)
        stmt = apply_sort(stmt, sort, SORT_ALLOWED)
        if sort is None:
            stmt = stmt.order_by(FarmMember.created_at.asc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.offset(page.offset).limit(page.limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total

    async def remove(self, farm_id: int, member_id: int, actor: FarmMember) -> None:
        target = await self._get(farm_id, member_id)
        self._assert_can_manage(actor, target)
        if target.role is FarmRole.OWNER and await self._count_owners(farm_id) == 1:
            raise ConflictError("Cannot remove the last owner of the farm")
        await self.db.delete(target)
        await self.db.commit()

    async def change_role(
        self, farm_id: int, member_id: int, new_role: FarmRole, actor: FarmMember
    ) -> FarmMember:
        target = await self._get(farm_id, member_id)
        self._assert_can_manage(actor, target)
        if new_role is FarmRole.OWNER and actor.role is not FarmRole.OWNER:
            raise ForbiddenError("Only an owner can grant the owner role")
        if (
            target.role is FarmRole.OWNER
            and new_role is not FarmRole.OWNER
            and await self._count_owners(farm_id) == 1
        ):
            raise ConflictError("Cannot demote the last owner of the farm")
        target.role = new_role
        await self.db.commit()
        return await self._get_with_user(farm_id, member_id)

    def _assert_can_manage(self, actor: FarmMember, target: FarmMember) -> None:
        # Admins may manage members and other admins, but only an owner manages an owner.
        if target.role is FarmRole.OWNER and actor.role is not FarmRole.OWNER:
            raise ForbiddenError("Only an owner can manage an owner")

    async def _count_owners(self, farm_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(FarmMember)
            .where(FarmMember.farm_id == farm_id, FarmMember.role == FarmRole.OWNER)
        )
        return (await self.db.execute(stmt)).scalar_one()

    async def _get(self, farm_id: int, member_id: int) -> FarmMember:
        stmt = select(FarmMember).where(FarmMember.id == member_id, FarmMember.farm_id == farm_id)
        member = (await self.db.execute(stmt)).scalar_one_or_none()
        if member is None:
            raise NotFoundError("Member not found")
        return member

    async def _get_with_user(self, farm_id: int, member_id: int) -> FarmMember:
        stmt = (
            select(FarmMember)
            .where(FarmMember.id == member_id, FarmMember.farm_id == farm_id)
            .options(selectinload(FarmMember.user))
        )
        return (await self.db.execute(stmt)).scalar_one()
