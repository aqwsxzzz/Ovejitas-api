from httpx import AsyncClient

from tests.conftest import AuthedUser

ANIMAL_INDIVIDUAL = {"name": "Cattle", "kind": "animal", "mode": "individual"}


async def _create_individual_asset(client: AsyncClient, authed: AuthedUser) -> int:
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/assets",
        headers=authed.headers,
        json=ANIMAL_INDIVIDUAL,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class TestOptionalStringStripsAndCoerces:
    async def test_whitespace_only_optional_name_becomes_null(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_individual_asset(client, authed_user)

        resp = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{asset_id}/individuals",
            headers=authed_user.headers,
            json={"tag": "T1", "name": "   "},
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["name"] is None

    async def test_padded_optional_name_is_stripped(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_individual_asset(client, authed_user)

        resp = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{asset_id}/individuals",
            headers=authed_user.headers,
            json={"tag": "T2", "name": "  Dolly  "},
        )

        assert resp.status_code == 201
        assert resp.json()["name"] == "Dolly"

    async def test_padded_required_tag_is_stripped(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_individual_asset(client, authed_user)

        resp = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{asset_id}/individuals",
            headers=authed_user.headers,
            json={"tag": "  T3  "},
        )

        assert resp.status_code == 201
        assert resp.json()["tag"] == "T3"


class TestRequiredStringRejectsWhitespace:
    async def test_whitespace_only_required_tag_returns_422(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_individual_asset(client, authed_user)

        resp = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{asset_id}/individuals",
            headers=authed_user.headers,
            json={"tag": "   "},
        )

        assert resp.status_code == 422

    async def test_whitespace_only_register_name_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "ws@example.com", "name": "   ", "password": "supersecret"},
        )
        assert resp.status_code == 422

    async def test_whitespace_only_farm_currency_returns_422(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.patch(
            f"/api/v1/farms/{authed_user.farm_id}",
            headers=authed_user.headers,
            json={"default_currency": "   "},
        )
        assert resp.status_code == 422
