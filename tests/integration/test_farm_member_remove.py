from collections.abc import Awaitable, Callable

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.farm_member.models import FarmRole
from tests.conftest import AuthedUser
from tests.integration._member_helpers import MEMBERS, add_member, owner_member_id


class TestRemoveMember:
    async def test_owner_removes_member_returns_204(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: Callable[[str], Awaitable[AuthedUser]],
        db_session: AsyncSession,
    ) -> None:
        member = await register_user("member@example.com")
        member_id = await add_member(
            db_session, user_id=member.user_id, farm_id=authed_user.farm_id, role=FarmRole.MEMBER
        )

        resp = await client.delete(
            f"{MEMBERS.format(farm_id=authed_user.farm_id)}/{member_id}",
            headers=authed_user.headers,
        )

        assert resp.status_code == 204, resp.text
        listed = await client.get(
            MEMBERS.format(farm_id=authed_user.farm_id), headers=authed_user.headers
        )
        assert listed.json()["meta"]["total"] == 1

    async def test_removing_last_owner_returns_409(
        self, client: AsyncClient, authed_user: AuthedUser, db_session: AsyncSession
    ) -> None:
        own_id = await owner_member_id(db_session, authed_user)

        resp = await client.delete(
            f"{MEMBERS.format(farm_id=authed_user.farm_id)}/{own_id}",
            headers=authed_user.headers,
        )

        assert resp.status_code == 409

    async def test_admin_cannot_remove_owner_returns_403(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: Callable[[str], Awaitable[AuthedUser]],
        db_session: AsyncSession,
    ) -> None:
        admin = await register_user("admin@example.com")
        await add_member(
            db_session, user_id=admin.user_id, farm_id=authed_user.farm_id, role=FarmRole.ADMIN
        )
        owner_id = await owner_member_id(db_session, authed_user)

        resp = await client.delete(
            f"{MEMBERS.format(farm_id=authed_user.farm_id)}/{owner_id}",
            headers=admin.headers,
        )

        assert resp.status_code == 403

    async def test_ordinary_member_cannot_remove_returns_403(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: Callable[[str], Awaitable[AuthedUser]],
        db_session: AsyncSession,
    ) -> None:
        member = await register_user("member@example.com")
        member_id = await add_member(
            db_session, user_id=member.user_id, farm_id=authed_user.farm_id, role=FarmRole.MEMBER
        )

        resp = await client.delete(
            f"{MEMBERS.format(farm_id=authed_user.farm_id)}/{member_id}",
            headers=member.headers,
        )

        assert resp.status_code == 403

    async def test_remove_unknown_member_returns_404(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.delete(
            f"{MEMBERS.format(farm_id=authed_user.farm_id)}/999999",
            headers=authed_user.headers,
        )

        assert resp.status_code == 404
