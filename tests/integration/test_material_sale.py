from httpx import AsyncClient

from tests.conftest import AuthedUser

MATERIAL = {"name": "Maíz", "kind": "material", "mode": "aggregated"}
ANIMAL_FLOCK = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}
EGGS = {"name": "Huevos", "kind": "material", "mode": "aggregated"}


def assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def events_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/events"


def sales_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/sales"


async def _create_asset(client: AsyncClient, authed: AuthedUser, body: dict[str, str]) -> int:
    resp = await client.post(assets_url(authed.farm_id), headers=authed.headers, json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _add_stock(
    client: AsyncClient, authed: AuthedUser, asset_id: int, quantity: str, unit: str = "kg"
) -> None:
    resp = await client.post(
        events_url(authed.farm_id, asset_id),
        headers=authed.headers,
        json={
            "type": "inventory",
            "occurred_at": "2026-04-01T10:00:00Z",
            "adjustment": "increment",
            "quantity": quantity,
            "unit": unit,
        },
    )
    assert resp.status_code == 201, resp.text


async def _events(
    client: AsyncClient, authed: AuthedUser, asset_id: int, event_type: str
) -> list[dict[str, object]]:
    resp = await client.get(
        events_url(authed.farm_id, asset_id),
        headers=authed.headers,
        params={"type": event_type},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


class TestMaterialSale:
    async def test_sale_decrements_stock_and_books_income(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL)
        await _add_stock(client, authed_user, asset_id, "100")

        resp = await client.post(
            sales_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"quantity": "30", "unit": "kg", "amount": "45.00"},
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["on_hand"] == "70"
        income = await _events(client, authed_user, asset_id, "income")
        assert len(income) == 1
        assert income[0]["amount"] == "45.00"
        assert income[0]["currency_id"] is not None

    async def test_income_event_carries_buyer(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL)
        await _add_stock(client, authed_user, asset_id, "100")

        resp = await client.post(
            sales_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"quantity": "10", "unit": "kg", "amount": "20.00", "buyer": "Mercado Central"},
        )

        assert resp.status_code == 201, resp.text
        income = await _events(client, authed_user, asset_id, "income")
        assert income[0]["payload"]["buyer"] == "Mercado Central"
        assert income[0]["payload"]["source"] == "material_sale"

    async def test_overselling_rejected_and_writes_nothing(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL)
        await _add_stock(client, authed_user, asset_id, "10")

        resp = await client.post(
            sales_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"quantity": "50", "unit": "kg", "amount": "75.00"},
        )

        assert resp.status_code == 409
        assert await _events(client, authed_user, asset_id, "income") == []
        # only the stock-seeding increment survives; the sale decrement rolled back
        assert len(await _events(client, authed_user, asset_id, "inventory")) == 1

    async def test_unit_not_in_stock_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL)
        await _add_stock(client, authed_user, asset_id, "100", unit="kg")

        resp = await client.post(
            sales_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"quantity": "5", "unit": "l", "amount": "10.00"},
        )

        assert resp.status_code == 422

    async def test_sale_on_non_material_asset_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_FLOCK)

        resp = await client.post(
            sales_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"quantity": "5", "unit": "kg", "amount": "10.00"},
        )

        assert resp.status_code == 422

    async def test_zero_amount_rejected(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL)
        await _add_stock(client, authed_user, asset_id, "100")

        resp = await client.post(
            sales_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"quantity": "5", "unit": "kg", "amount": "0"},
        )

        assert resp.status_code == 422


class TestProductionToIncomeLoop:
    async def test_harvest_then_sale_closes_the_loop(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        eggs_id = await _create_asset(client, authed_user, EGGS)
        flock_id = await _create_asset(client, authed_user, ANIMAL_FLOCK)
        linked = await client.patch(
            f"{assets_url(authed_user.farm_id)}/{flock_id}",
            headers=authed_user.headers,
            json={"produce_asset_id": eggs_id},
        )
        assert linked.status_code == 200, linked.text

        category = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/event-categories",
            headers=authed_user.headers,
            json={"type": "production", "name": "Huevos", "unit": "unit"},
        )
        assert category.status_code == 201, category.text

        harvested = await client.post(
            f"{assets_url(authed_user.farm_id)}/{flock_id}/harvests",
            headers=authed_user.headers,
            json={"quantity": "20", "unit": "unit", "category_id": category.json()["id"]},
        )
        assert harvested.status_code == 201, harvested.text

        sold = await client.post(
            sales_url(authed_user.farm_id, eggs_id),
            headers=authed_user.headers,
            json={"quantity": "5", "unit": "unit", "amount": "12.50"},
        )

        assert sold.status_code == 201, sold.text
        assert sold.json()["on_hand"] == "15"
