from collections.abc import Awaitable, Callable

from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.farm_member.models import FarmMember, FarmRole
from tests.conftest import AuthedUser

INVITES = "/api/v1/farms/{farm_id}/invitations"


async def _create_invite(
    client: AsyncClient, owner: AuthedUser, email: str, role: str = "member"
) -> Response:
    return await client.post(
        INVITES.format(farm_id=owner.farm_id),
        headers=owner.headers,
        json={"email": email, "role": role},
    )


class TestCreateInvitation:
    async def test_owner_can_create_invitation_returns_token(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await _create_invite(client, authed_user, "invitee@example.com")

        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["token"]
        assert body["invitation"]["status"] == "pending"
        assert body["invitation"]["email"] == "invitee@example.com"
        assert "token_hash" not in body["invitation"]

    async def test_invite_as_owner_role_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await _create_invite(client, authed_user, "invitee@example.com", role="owner")
        assert resp.status_code == 422

    async def test_inviting_an_existing_member_returns_409(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await _create_invite(client, authed_user, "default@example.com")
        assert resp.status_code == 409

    async def test_duplicate_pending_invite_returns_409(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await _create_invite(client, authed_user, "invitee@example.com")
        resp = await _create_invite(client, authed_user, "invitee@example.com")
        assert resp.status_code == 409

    async def test_member_cannot_create_invitation_returns_403(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: Callable[[str], Awaitable[AuthedUser]],
        db_session: AsyncSession,
    ) -> None:
        other = await register_user("member@example.com")
        db_session.add(
            FarmMember(user_id=other.user_id, farm_id=authed_user.farm_id, role=FarmRole.MEMBER)
        )
        await db_session.commit()

        resp = await client.post(
            INVITES.format(farm_id=authed_user.farm_id),
            headers=other.headers,
            json={"email": "invitee@example.com", "role": "member"},
        )
        assert resp.status_code == 403

    async def test_non_member_cannot_create_invitation_returns_403(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        outsider = await register_user("outsider@example.com")
        resp = await client.post(
            INVITES.format(farm_id=authed_user.farm_id),
            headers=outsider.headers,
            json={"email": "invitee@example.com", "role": "member"},
        )
        assert resp.status_code == 403


class TestListAndRevokeInvitation:
    async def test_list_returns_created_invitation(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await _create_invite(client, authed_user, "invitee@example.com")

        resp = await client.get(
            INVITES.format(farm_id=authed_user.farm_id), headers=authed_user.headers
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["total"] == 1
        assert body["data"][0]["email"] == "invitee@example.com"

    async def test_revoke_makes_token_unresolvable(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        created = await _create_invite(client, authed_user, "invitee@example.com")
        invite_id = created.json()["invitation"]["id"]
        token = created.json()["token"]

        revoke = await client.post(
            f"{INVITES.format(farm_id=authed_user.farm_id)}/{invite_id}/revoke",
            headers=authed_user.headers,
        )
        assert revoke.status_code == 204

        resolved = await client.get(f"/api/v1/invitations/{token}")
        assert resolved.status_code == 404


class TestResolveInvitation:
    async def test_resolve_unknown_email_requires_registration(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        created = await _create_invite(client, authed_user, "brand-new@example.com")
        token = created.json()["token"]

        resp = await client.get(f"/api/v1/invitations/{token}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["requires_registration"] is True
        assert body["farm_id"] == authed_user.farm_id
        assert body["role"] == "member"

    async def test_resolve_existing_email_does_not_require_registration(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        await register_user("known@example.com")
        created = await _create_invite(client, authed_user, "known@example.com")
        token = created.json()["token"]

        resp = await client.get(f"/api/v1/invitations/{token}")

        assert resp.status_code == 200
        assert resp.json()["requires_registration"] is False
