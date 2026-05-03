from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.farm.models import Farm
from ovejitas.features.farm_member.models import FarmMember, FarmRole
from ovejitas.features.user.models import User
from tests.factories import FACTORY_PASSWORD, UserFactory

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
ME = "/api/v1/auth/me"


class TestRegister:
    async def test_creates_user_farm_and_owner_membership(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        response = await client.post(
            REGISTER,
            json={"email": "alice@example.com", "name": "Alice", "password": "supersecret"},
        )

        assert response.status_code == 201
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body

        user = (
            await db_session.execute(select(User).where(User.email == "alice@example.com"))
        ).scalar_one()
        farm = (await db_session.execute(select(Farm))).scalar_one()
        membership = (await db_session.execute(select(FarmMember))).scalar_one()

        assert farm.name == "My Farm"
        assert farm.default_currency == "USD"
        assert membership.user_id == user.id
        assert membership.farm_id == farm.id
        assert membership.role == FarmRole.OWNER

    async def test_duplicate_email_returns_409(self, client: AsyncClient) -> None:
        payload = {"email": "dup@example.com", "name": "Dup", "password": "supersecret"}
        first = await client.post(REGISTER, json=payload)
        assert first.status_code == 201

        second = await client.post(REGISTER, json=payload)
        assert second.status_code == 409
        assert second.json()["code"] == "conflict"

    async def test_short_password_rejected_by_schema(self, client: AsyncClient) -> None:
        response = await client.post(
            REGISTER,
            json={"email": "short@example.com", "name": "Short", "password": "abc"},
        )
        assert response.status_code == 422

    async def test_invalid_email_rejected_by_schema(self, client: AsyncClient) -> None:
        response = await client.post(
            REGISTER,
            json={"email": "not-an-email", "name": "Bad", "password": "supersecret"},
        )
        assert response.status_code == 422


class TestLogin:
    async def test_with_valid_credentials_returns_tokens(self, client: AsyncClient) -> None:
        user = await UserFactory.create_async()

        response = await client.post(
            LOGIN, json={"email": user.email, "password": FACTORY_PASSWORD}
        )

        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_wrong_password_returns_401(self, client: AsyncClient) -> None:
        user = await UserFactory.create_async()

        response = await client.post(
            LOGIN, json={"email": user.email, "password": "wrong-password"}
        )

        assert response.status_code == 401

    async def test_unknown_email_returns_401(self, client: AsyncClient) -> None:
        response = await client.post(
            LOGIN, json={"email": "nobody@example.com", "password": "whatever123"}
        )

        assert response.status_code == 401


class TestMe:
    async def test_valid_token_returns_user_and_memberships(self, client: AsyncClient) -> None:
        registered = await client.post(
            REGISTER,
            json={"email": "dave@example.com", "name": "Dave", "password": "supersecret"},
        )
        token = registered.json()["access_token"]

        response = await client.get(ME, headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        body = response.json()
        assert body["user"]["email"] == "dave@example.com"
        assert len(body["memberships"]) == 1
        assert body["memberships"][0]["role"] == "owner"
        assert body["memberships"][0]["default_currency"] == "USD"

    async def test_without_token_returns_401(self, client: AsyncClient) -> None:
        response = await client.get(ME)
        assert response.status_code == 401

    async def test_invalid_token_returns_401(self, client: AsyncClient) -> None:
        response = await client.get(ME, headers={"Authorization": "Bearer garbage"})
        assert response.status_code == 401


class TestRefresh:
    async def test_exchanges_refresh_for_new_tokens(self, client: AsyncClient) -> None:
        registered = await client.post(
            REGISTER,
            json={"email": "eve@example.com", "name": "Eve", "password": "supersecret"},
        )
        refresh_token = registered.json()["refresh_token"]

        response = await client.post(REFRESH, json={"refresh_token": refresh_token})

        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_access_token_used_as_refresh_returns_401(self, client: AsyncClient) -> None:
        registered = await client.post(
            REGISTER,
            json={"email": "frank@example.com", "name": "Frank", "password": "supersecret"},
        )
        access_token = registered.json()["access_token"]

        response = await client.post(REFRESH, json={"refresh_token": access_token})

        assert response.status_code == 401
