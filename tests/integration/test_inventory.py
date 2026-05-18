from httpx import AsyncClient

from tests.conftest import AuthedUser

MATERIAL_AGGREGATED = {"name": "Maíz", "kind": "material", "mode": "aggregated"}
ANIMAL_AGGREGATED = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}
ANIMAL_INDIVIDUAL = {"name": "Vacas", "kind": "animal", "mode": "individual"}


def assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def events_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/events"


def balance_url(farm_id: int, asset_id: int) -> str:
    return f"{events_url(farm_id, asset_id)}/balance"


def inventory_summary_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/reports/inventory-summary"


async def _create_asset(client: AsyncClient, authed: AuthedUser, payload: dict) -> int:
    resp = await client.post(assets_url(authed.farm_id), headers=authed.headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _post_inventory(
    client: AsyncClient,
    authed: AuthedUser,
    asset_id: int,
    adjustment: str,
    quantity: str,
    unit: str = "kg",
    occurred_at: str = "2026-04-20T10:00:00Z",
) -> dict:
    resp = await client.post(
        events_url(authed.farm_id, asset_id),
        headers=authed.headers,
        json={
            "type": "inventory",
            "occurred_at": occurred_at,
            "adjustment": adjustment,
            "quantity": quantity,
            "unit": unit,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestCreateInventory:
    async def test_increment_ok(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL_AGGREGATED)
        body = await _post_inventory(client, authed_user, asset_id, "increment", "10")
        assert body["type"] == "inventory"
        assert body["adjustment"] == "increment"
        assert body["quantity"] == "10"
        assert body["unit"] == "kg"

    async def test_reset_allows_zero(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL_AGGREGATED)
        body = await _post_inventory(client, authed_user, asset_id, "reset", "0")
        assert body["adjustment"] == "reset"
        assert body["quantity"] == "0"

    async def test_increment_zero_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL_AGGREGATED)
        resp = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "inventory",
                "occurred_at": "2026-04-20T10:00:00Z",
                "adjustment": "increment",
                "quantity": "0",
                "unit": "kg",
            },
        )
        assert resp.status_code == 422

    async def test_aggregated_animal_asset_accepted(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        resp = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "inventory",
                "occurred_at": "2026-04-20T10:00:00Z",
                "adjustment": "increment",
                "quantity": "10",
                "unit": "head",
            },
        )
        assert resp.status_code == 201, resp.text

    async def test_individual_mode_asset_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        resp = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "inventory",
                "occurred_at": "2026-04-20T10:00:00Z",
                "adjustment": "increment",
                "quantity": "10",
                "unit": "head",
            },
        )
        assert resp.status_code == 422


class TestBalance:
    async def test_balance_derived_from_event_stream(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL_AGGREGATED)
        await _post_inventory(
            client, authed_user, asset_id, "reset", "100", occurred_at="2026-04-01T10:00:00Z"
        )
        await _post_inventory(
            client, authed_user, asset_id, "increment", "50", occurred_at="2026-04-05T10:00:00Z"
        )
        await _post_inventory(
            client, authed_user, asset_id, "decrement", "20", occurred_at="2026-04-10T10:00:00Z"
        )

        resp = await client.get(
            balance_url(authed_user.farm_id, asset_id), headers=authed_user.headers
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["asset_id"] == asset_id
        assert body["balances"] == [
            {"unit": "kg", "on_hand": "130", "last_reset_at": "2026-04-01T10:00:00Z"}
        ]

    async def test_balance_per_unit(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL_AGGREGATED)
        await _post_inventory(client, authed_user, asset_id, "increment", "10", unit="kg")
        await _post_inventory(client, authed_user, asset_id, "increment", "5", unit="l")

        resp = await client.get(
            balance_url(authed_user.farm_id, asset_id), headers=authed_user.headers
        )
        assert resp.status_code == 200, resp.text
        balances = {b["unit"]: b["on_hand"] for b in resp.json()["balances"]}
        assert balances == {"kg": "10", "l": "5"}

    async def test_reset_clears_prior_history(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL_AGGREGATED)
        await _post_inventory(
            client, authed_user, asset_id, "increment", "999", occurred_at="2026-04-01T10:00:00Z"
        )
        await _post_inventory(
            client, authed_user, asset_id, "reset", "10", occurred_at="2026-04-02T10:00:00Z"
        )

        resp = await client.get(
            balance_url(authed_user.farm_id, asset_id), headers=authed_user.headers
        )
        assert resp.json()["balances"][0]["on_hand"] == "10"


class TestInventorySummaryReport:
    async def test_summary_lists_each_material_asset(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        a = await _create_asset(
            client, authed_user, {"name": "Maíz", "kind": "material", "mode": "aggregated"}
        )
        b = await _create_asset(
            client, authed_user, {"name": "Sal", "kind": "material", "mode": "aggregated"}
        )
        await _post_inventory(client, authed_user, a, "increment", "30", unit="kg")
        await _post_inventory(client, authed_user, b, "increment", "5", unit="kg")

        resp = await client.get(
            inventory_summary_url(authed_user.farm_id), headers=authed_user.headers
        )
        assert resp.status_code == 200, resp.text
        rows = {(r["asset_id"], r["unit"]): r["on_hand"] for r in resp.json()["data"]}
        assert rows == {(a, "kg"): "30", (b, "kg"): "5"}
