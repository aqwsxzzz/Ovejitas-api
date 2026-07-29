from httpx import AsyncClient

from tests.conftest import AuthedUser

FARM = "/api/v1/farms/{farm_id}"


class TestGetFarm:
    async def test_member_can_read_own_farm(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.get(
            FARM.format(farm_id=authed_user.farm_id),
            headers=authed_user.headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == authed_user.farm_id
        assert body["default_currency"] == "USD"
        assert body["timezone"] == "UTC"

    async def test_non_member_returns_403(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.get(
            FARM.format(farm_id=authed_user.farm_id + 999),
            headers=authed_user.headers,
        )
        assert resp.status_code == 403

    async def test_anonymous_returns_401(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.get(FARM.format(farm_id=authed_user.farm_id))
        assert resp.status_code == 401


class TestUpdateFarm:
    async def test_member_can_change_currency_uppercased(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.patch(
            FARM.format(farm_id=authed_user.farm_id),
            headers=authed_user.headers,
            json={"default_currency": "eur"},
        )

        assert resp.status_code == 200
        assert resp.json()["default_currency"] == "EUR"

    async def test_non_alpha_currency_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.patch(
            FARM.format(farm_id=authed_user.farm_id),
            headers=authed_user.headers,
            json={"default_currency": "12$"},
        )
        assert resp.status_code == 422

    async def test_short_currency_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.patch(
            FARM.format(farm_id=authed_user.farm_id),
            headers=authed_user.headers,
            json={"default_currency": "US"},
        )
        assert resp.status_code == 422

    async def test_member_can_set_iana_timezone(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.patch(
            FARM.format(farm_id=authed_user.farm_id),
            headers=authed_user.headers,
            json={"timezone": "America/Montevideo"},
        )

        assert resp.status_code == 200
        assert resp.json()["timezone"] == "America/Montevideo"

    async def test_unknown_timezone_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.patch(
            FARM.format(farm_id=authed_user.farm_id),
            headers=authed_user.headers,
            json={"timezone": "Mars/Olympus_Mons"},
        )
        assert resp.status_code == 422

    async def test_unknown_field_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.patch(
            FARM.format(farm_id=authed_user.farm_id),
            headers=authed_user.headers,
            json={"bogus": "x"},
        )
        assert resp.status_code == 422

    async def test_non_member_cannot_update(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.patch(
            FARM.format(farm_id=authed_user.farm_id + 999),
            headers=authed_user.headers,
            json={"default_currency": "EUR"},
        )
        assert resp.status_code == 403


class TestEventInheritsFarmCurrency:
    async def test_expense_currency_is_stamped_from_farm(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await client.patch(
            FARM.format(farm_id=authed_user.farm_id),
            headers=authed_user.headers,
            json={"default_currency": "EUR"},
        )
        asset = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets",
            headers=authed_user.headers,
            json={"name": "Crop", "kind": "crop", "mode": "aggregated"},
        )
        asset_id = asset.json()["id"]

        resp = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{asset_id}/events",
            headers=authed_user.headers,
            json={
                "type": "expense",
                "occurred_at": "2026-01-01T00:00:00Z",
                "amount": "42.00",
            },
        )

        assert resp.status_code == 201, resp.text
        # The expense inherits the farm's preferred currency by id — changing the
        # default to EUR ensured an EUR currency row, and the event points at it.
        currency_id = resp.json()["currency_id"]
        assert currency_id is not None
        listing = await client.get(
            f"/api/v1/farms/{authed_user.farm_id}/currencies", headers=authed_user.headers
        )
        eur = next(c for c in listing.json()["data"] if c["code"] == "EUR")
        assert currency_id == eur["id"]

    async def test_currency_field_in_body_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets",
            headers=authed_user.headers,
            json={"name": "Crop", "kind": "crop", "mode": "aggregated"},
        )
        asset_id = asset.json()["id"]

        resp = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{asset_id}/events",
            headers=authed_user.headers,
            json={
                "type": "expense",
                "occurred_at": "2026-01-01T00:00:00Z",
                "amount": "10",
                "currency": "USD",
            },
        )
        assert resp.status_code == 422
