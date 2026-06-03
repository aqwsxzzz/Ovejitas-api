from collections.abc import Awaitable, Callable

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.farm_member.models import FarmRole
from tests.conftest import AuthedUser
from tests.integration._member_helpers import MEMBERS, add_member


class TestListMembers:
    async def test_list_returns_owner_with_nested_user(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.get(
            MEMBERS.format(farm_id=authed_user.farm_id), headers=authed_user.headers
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["meta"]["total"] == 1
        row = body["data"][0]
        assert row["role"] == "owner"
        assert row["user"]["email"] == "default@example.com"
        assert "password_hash" not in row["user"]

    async def test_role_filter_returns_only_matching_role(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: Callable[[str], Awaitable[AuthedUser]],
        db_session: AsyncSession,
    ) -> None:
        other = await register_user("member@example.com")
        await add_member(
            db_session, user_id=other.user_id, farm_id=authed_user.farm_id, role=FarmRole.MEMBER
        )

        resp = await client.get(
            MEMBERS.format(farm_id=authed_user.farm_id),
            headers=authed_user.headers,
            params={"role": "member"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["total"] == 1
        assert body["data"][0]["user"]["email"] == "member@example.com"

    async def test_ordinary_member_can_view_member_list(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: Callable[[str], Awaitable[AuthedUser]],
        db_session: AsyncSession,
    ) -> None:
        member = await register_user("member@example.com")
        await add_member(
            db_session, user_id=member.user_id, farm_id=authed_user.farm_id, role=FarmRole.MEMBER
        )

        resp = await client.get(MEMBERS.format(farm_id=authed_user.farm_id), headers=member.headers)

        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] == 2

    async def test_non_member_cannot_list_returns_403(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        outsider = await register_user("outsider@example.com")

        resp = await client.get(
            MEMBERS.format(farm_id=authed_user.farm_id), headers=outsider.headers
        )

        assert resp.status_code == 403
