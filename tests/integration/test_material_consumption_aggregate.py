from decimal import Decimal

from httpx import AsyncClient

from tests.conftest import AuthedUser

MATERIAL = {"name": "Maíz", "kind": "material", "mode": "aggregated"}
ANIMAL = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}


def _assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def _consumptions_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/material-consumptions"


def _aggregate_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/reports/material-consumption-aggregate"


async def _create_asset(client: AsyncClient, authed: AuthedUser, payload: dict) -> int:
    resp = await client.post(_assets_url(authed.farm_id), headers=authed.headers, json=payload)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _increment(client: AsyncClient, authed: AuthedUser, asset_id: int, quantity: str) -> None:
    resp = await client.post(
        f"{_assets_url(authed.farm_id)}/{asset_id}/events",
        headers=authed.headers,
        json={
            "type": "inventory",
            "occurred_at": "2026-04-01T10:00:00Z",
            "adjustment": "increment",
            "quantity": quantity,
            "unit": "kg",
        },
    )
    assert resp.status_code == 201, resp.text


async def _consume(
    client: AsyncClient,
    authed: AuthedUser,
    *,
    material_id: int,
    consumer_id: int,
    quantity: str,
    reason: str = "feeding",
    occurred_at: str = "2026-04-06T10:00:00Z",
) -> None:
    payload: dict = {
        "material_asset_id": material_id,
        "consumer_asset_id": consumer_id,
        "occurred_at": occurred_at,
        "quantity": quantity,
        "unit": "kg",
        "reason": reason,
    }
    if reason != "feeding":
        del payload["consumer_asset_id"]
    resp = await client.post(
        _consumptions_url(authed.farm_id), headers=authed.headers, json=payload
    )
    assert resp.status_code == 201, resp.text


async def _setup(client: AsyncClient, authed: AuthedUser) -> tuple[int, int]:
    material_id = await _create_asset(client, authed, MATERIAL)
    animal_id = await _create_asset(client, authed, ANIMAL)
    await _increment(client, authed, material_id, "1000")
    return material_id, animal_id


class TestListConsumptions:
    async def test_list_returns_created_consumptions(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user)
        await _consume(
            client, authed_user, material_id=material_id, consumer_id=animal_id, quantity="30"
        )

        resp = await client.get(_consumptions_url(authed_user.farm_id), headers=authed_user.headers)

        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] == 1

    async def test_list_filters_by_reason(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user)
        await _consume(
            client, authed_user, material_id=material_id, consumer_id=animal_id, quantity="30"
        )
        await _consume(
            client,
            authed_user,
            material_id=material_id,
            consumer_id=animal_id,
            quantity="10",
            reason="spoilage",
        )

        resp = await client.get(
            _consumptions_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"reason": "spoilage"},
        )

        assert resp.status_code == 200, resp.text
        rows = resp.json()["data"]
        assert [r["reason"] for r in rows] == ["spoilage"]


class TestAggregateReport:
    async def test_weekly_bucket_sums_quantity_across_days(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user)
        await _consume(
            client,
            authed_user,
            material_id=material_id,
            consumer_id=animal_id,
            quantity="30",
            occurred_at="2026-04-06T10:00:00Z",
        )
        await _consume(
            client,
            authed_user,
            material_id=material_id,
            consumer_id=animal_id,
            quantity="20",
            occurred_at="2026-04-07T10:00:00Z",
        )

        resp = await client.get(
            _aggregate_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"bucket": "week", "group_by": "material"},
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["data"]) == 1
        assert Decimal(body["totals"][0]["total_qty"]) == Decimal("50")
        assert body["totals"][0]["unit"] == "kg"

    async def test_daily_bucket_splits_quantity_by_day(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user)
        await _consume(
            client,
            authed_user,
            material_id=material_id,
            consumer_id=animal_id,
            quantity="30",
            occurred_at="2026-04-06T10:00:00Z",
        )
        await _consume(
            client,
            authed_user,
            material_id=material_id,
            consumer_id=animal_id,
            quantity="20",
            occurred_at="2026-04-07T10:00:00Z",
        )

        resp = await client.get(
            _aggregate_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"bucket": "day", "group_by": "material"},
        )

        assert resp.status_code == 200, resp.text
        assert len(resp.json()["data"]) == 2

    async def test_group_by_consumer_keys_rows_to_the_animal(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user)
        await _consume(
            client, authed_user, material_id=material_id, consumer_id=animal_id, quantity="40"
        )

        resp = await client.get(
            _aggregate_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"bucket": "day", "group_by": "consumer"},
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["data"][0]["group"] == str(animal_id)
