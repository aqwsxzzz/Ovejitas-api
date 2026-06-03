from collections.abc import Awaitable, Callable

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.farm_member.models import FarmRole
from tests.conftest import AuthedUser
from tests.integration._member_helpers import MEMBERS, add_member, owner_member_id


def _patch_url(farm_id: int, member_id: int) -> str:
    return f"{MEMBERS.format(farm_id=farm_id)}/{member_id}"


class TestChangeRole:
    async def test_owner_promotes_member_to_admin_returns_updated_role(
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

        resp = await client.patch(
            _patch_url(authed_user.farm_id, member_id),
            headers=authed_user.headers,
            json={"role": "admin"},
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["role"] == "admin"
        assert body["user"]["email"] == "member@example.com"

    async def test_owner_can_grant_owner_role(
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

        resp = await client.patch(
            _patch_url(authed_user.farm_id, member_id),
            headers=authed_user.headers,
            json={"role": "owner"},
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["role"] == "owner"

    async def test_admin_cannot_grant_owner_role_returns_403(
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
        member = await register_user("member@example.com")
        member_id = await add_member(
            db_session, user_id=member.user_id, farm_id=authed_user.farm_id, role=FarmRole.MEMBER
        )

        resp = await client.patch(
            _patch_url(authed_user.farm_id, member_id),
            headers=admin.headers,
            json={"role": "owner"},
        )

        assert resp.status_code == 403

    async def test_admin_cannot_modify_owner_returns_403(
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

        resp = await client.patch(
            _patch_url(authed_user.farm_id, owner_id),
            headers=admin.headers,
            json={"role": "member"},
        )

        assert resp.status_code == 403

    async def test_demoting_last_owner_returns_409(
        self, client: AsyncClient, authed_user: AuthedUser, db_session: AsyncSession
    ) -> None:
        owner_id = await owner_member_id(db_session, authed_user)

        resp = await client.patch(
            _patch_url(authed_user.farm_id, owner_id),
            headers=authed_user.headers,
            json={"role": "member"},
        )

        assert resp.status_code == 409

    async def test_ordinary_member_cannot_change_role_returns_403(
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

        resp = await client.patch(
            _patch_url(authed_user.farm_id, member_id),
            headers=member.headers,
            json={"role": "admin"},
        )

        assert resp.status_code == 403

    async def test_change_role_unknown_member_returns_404(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.patch(
            _patch_url(authed_user.farm_id, 999999),
            headers=authed_user.headers,
            json={"role": "admin"},
        )

        assert resp.status_code == 404
