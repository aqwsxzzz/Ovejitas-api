from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.farm_invitation.models import FarmInvitation
from ovejitas.features.farm_member.models import FarmMember, FarmRole
from tests.conftest import AuthedUser

INVITES = "/api/v1/farms/{farm_id}/invitations"
ACCEPT = "/api/v1/invitations/{token}/accept"
ME = "/api/v1/auth/me"

# Password used by the register_user/authed_user fixtures.
FIXTURE_PASSWORD = "password123"


async def _invite_token(client: AsyncClient, owner: AuthedUser, email: str) -> str:
    resp = await client.post(
        INVITES.format(farm_id=owner.farm_id),
        headers=owner.headers,
        json={"email": email, "role": "member"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["token"]


class TestAcceptAsNewUser:
    async def test_new_user_accept_joins_only_invited_farm(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        token = await _invite_token(client, authed_user, "newbie@example.com")

        resp = await client.post(
            ACCEPT.format(token=token),
            json={"password": "newpassword1", "name": "Newbie"},
        )

        assert resp.status_code == 200, resp.text
        access = resp.json()["access_token"]
        me = await client.get(ME, headers={"Authorization": f"Bearer {access}"})
        memberships = me.json()["memberships"]
        assert len(memberships) == 1
        assert memberships[0]["farm_id"] == authed_user.farm_id
        assert memberships[0]["role"] == "member"

    async def test_new_user_accept_without_name_returns_422(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        token = await _invite_token(client, authed_user, "newbie@example.com")
        resp = await client.post(ACCEPT.format(token=token), json={"password": "newpassword1"})
        assert resp.status_code == 422


class TestAcceptAsExistingUser:
    async def test_existing_user_accept_lists_both_farms(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        existing = await register_user("existing@example.com")
        token = await _invite_token(client, authed_user, "existing@example.com")

        resp = await client.post(ACCEPT.format(token=token), json={"password": FIXTURE_PASSWORD})

        assert resp.status_code == 200, resp.text
        me = await client.get(ME, headers=existing.headers)
        farm_ids = {m["farm_id"] for m in me.json()["memberships"]}
        assert farm_ids == {existing.farm_id, authed_user.farm_id}

    async def test_existing_user_wrong_password_returns_401(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        await register_user("existing@example.com")
        token = await _invite_token(client, authed_user, "existing@example.com")

        resp = await client.post(ACCEPT.format(token=token), json={"password": "wrong-password"})
        assert resp.status_code == 401

    async def test_accept_when_already_member_returns_409(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: Callable[[str], Awaitable[AuthedUser]],
        db_session: AsyncSession,
    ) -> None:
        existing = await register_user("existing@example.com")
        token = await _invite_token(client, authed_user, "existing@example.com")
        db_session.add(
            FarmMember(user_id=existing.user_id, farm_id=authed_user.farm_id, role=FarmRole.MEMBER)
        )
        await db_session.commit()

        resp = await client.post(ACCEPT.format(token=token), json={"password": FIXTURE_PASSWORD})
        assert resp.status_code == 409


class TestAcceptTokenState:
    async def test_accept_same_token_twice_returns_409(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        token = await _invite_token(client, authed_user, "newbie@example.com")
        first = await client.post(
            ACCEPT.format(token=token), json={"password": "newpassword1", "name": "Newbie"}
        )
        assert first.status_code == 200, first.text

        second = await client.post(
            ACCEPT.format(token=token), json={"password": "newpassword1", "name": "Newbie"}
        )
        assert second.status_code == 409

    async def test_expired_token_returns_410(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        db_session: AsyncSession,
    ) -> None:
        created = await client.post(
            INVITES.format(farm_id=authed_user.farm_id),
            headers=authed_user.headers,
            json={"email": "newbie@example.com", "role": "member"},
        )
        invite_id = created.json()["invitation"]["id"]
        token = created.json()["token"]

        invite = await db_session.get(FarmInvitation, invite_id)
        assert invite is not None
        invite.expires_at = datetime.now(UTC) - timedelta(days=1)
        await db_session.commit()

        resp = await client.post(
            ACCEPT.format(token=token), json={"password": "newpassword1", "name": "Newbie"}
        )
        assert resp.status_code == 410
