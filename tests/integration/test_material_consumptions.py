from httpx import AsyncClient

from tests.conftest import AuthedUser

MATERIAL = {"name": "Maíz", "kind": "material", "mode": "aggregated"}
ANIMAL = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}


def _assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def _consumptions_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/material-consumptions"


def _balance_url(farm_id: int, asset_id: int) -> str:
    return f"{_assets_url(farm_id)}/{asset_id}/events/balance"


async def _create_asset(client: AsyncClient, authed: AuthedUser, payload: dict) -> int:
    resp = await client.post(_assets_url(authed.farm_id), headers=authed.headers, json=payload)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _increment(
    client: AsyncClient, authed: AuthedUser, asset_id: int, quantity: str, unit: str = "kg"
) -> None:
    resp = await client.post(
        f"{_assets_url(authed.farm_id)}/{asset_id}/events",
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


async def _on_hand(
    client: AsyncClient, authed: AuthedUser, asset_id: int, unit: str = "kg"
) -> str | None:
    resp = await client.get(_balance_url(authed.farm_id, asset_id), headers=authed.headers)
    assert resp.status_code == 200, resp.text
    for row in resp.json()["balances"]:
        if row["unit"] == unit:
            return str(row["on_hand"])
    return None


async def _setup(
    client: AsyncClient, authed: AuthedUser, *, stock: str | None = "100"
) -> tuple[int, int]:
    """Returns (material_asset_id, animal_asset_id); material pre-stocked in kg."""
    material_id = await _create_asset(client, authed, MATERIAL)
    animal_id = await _create_asset(client, authed, ANIMAL)
    if stock is not None:
        await _increment(client, authed, material_id, stock)
    return material_id, animal_id


async def _consume(
    client: AsyncClient,
    authed: AuthedUser,
    *,
    material_id: int,
    quantity: str = "30",
    reason: str = "feeding",
    consumer_id: int | None = None,
    unit: str = "kg",
    occurred_at: str = "2026-04-20T10:00:00Z",
    idempotency_key: str | None = None,
) -> object:
    payload: dict = {
        "material_asset_id": material_id,
        "occurred_at": occurred_at,
        "quantity": quantity,
        "unit": unit,
        "reason": reason,
    }
    if consumer_id is not None:
        payload["consumer_asset_id"] = consumer_id
    if idempotency_key is not None:
        payload["idempotency_key"] = idempotency_key
    return await client.post(
        _consumptions_url(authed.farm_id), headers=authed.headers, json=payload
    )


class TestCreateConsumption:
    async def test_create_feeding_decrements_material_stock(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user)

        resp = await _consume(
            client, authed_user, material_id=material_id, quantity="30", consumer_id=animal_id
        )

        assert resp.status_code == 201, resp.text
        assert await _on_hand(client, authed_user, material_id) == "70"

    async def test_create_waste_decrements_stock_without_consumer(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, _ = await _setup(client, authed_user)

        resp = await _consume(
            client, authed_user, material_id=material_id, quantity="15", reason="waste"
        )

        assert resp.status_code == 201, resp.text
        assert await _on_hand(client, authed_user, material_id) == "85"

    async def test_feeding_without_consumer_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, _ = await _setup(client, authed_user)

        resp = await _consume(client, authed_user, material_id=material_id, reason="feeding")

        assert resp.status_code == 422

    async def test_waste_with_consumer_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user)

        resp = await _consume(
            client, authed_user, material_id=material_id, reason="waste", consumer_id=animal_id
        )

        assert resp.status_code == 422

    async def test_consume_more_than_on_hand_is_rejected_with_409(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user, stock="10")

        resp = await _consume(
            client, authed_user, material_id=material_id, quantity="25", consumer_id=animal_id
        )

        assert resp.status_code == 409
        assert resp.json()["code"] == "insufficient_stock"

    async def test_rejected_oversell_leaves_stock_unchanged(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user, stock="10")

        await _consume(
            client, authed_user, material_id=material_id, quantity="25", consumer_id=animal_id
        )

        assert await _on_hand(client, authed_user, material_id) == "10"

    async def test_consume_in_unit_without_stock_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user)

        resp = await _consume(
            client, authed_user, material_id=material_id, unit="l", consumer_id=animal_id
        )

        assert resp.status_code == 422

    async def test_material_must_be_a_material_asset(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        _, animal_id = await _setup(client, authed_user, stock=None)

        resp = await _consume(client, authed_user, material_id=animal_id, reason="waste")

        assert resp.status_code == 422

    async def test_consumer_must_be_an_animal_asset(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, _ = await _setup(client, authed_user)

        resp = await _consume(client, authed_user, material_id=material_id, consumer_id=material_id)

        assert resp.status_code == 422

    async def test_material_from_another_farm_is_not_found(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: object,
    ) -> None:
        await _setup(client, authed_user)
        other = await register_user("other@example.com")  # type: ignore[operator]
        other_material = await _create_asset(client, other, MATERIAL)
        await _increment(client, other, other_material, "100")

        resp = await _consume(client, authed_user, material_id=other_material, reason="waste")

        assert resp.status_code in (403, 404)


class TestUpdateConsumption:
    async def test_update_quantity_reconciles_stock(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user)
        created = await _consume(
            client, authed_user, material_id=material_id, quantity="30", consumer_id=animal_id
        )
        consumption_id = created.json()["id"]  # type: ignore[attr-defined]

        resp = await client.patch(
            f"{_consumptions_url(authed_user.farm_id)}/{consumption_id}",
            headers=authed_user.headers,
            json={"quantity": "50"},
        )

        assert resp.status_code == 200, resp.text
        assert await _on_hand(client, authed_user, material_id) == "50"

    async def test_update_quantity_over_stock_is_rejected_with_409(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user, stock="40")
        created = await _consume(
            client, authed_user, material_id=material_id, quantity="30", consumer_id=animal_id
        )
        consumption_id = created.json()["id"]  # type: ignore[attr-defined]

        resp = await client.patch(
            f"{_consumptions_url(authed_user.farm_id)}/{consumption_id}",
            headers=authed_user.headers,
            json={"quantity": "100"},
        )

        assert resp.status_code == 409

    async def test_material_asset_id_is_immutable(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user)
        created = await _consume(
            client, authed_user, material_id=material_id, consumer_id=animal_id
        )
        consumption_id = created.json()["id"]  # type: ignore[attr-defined]

        resp = await client.patch(
            f"{_consumptions_url(authed_user.farm_id)}/{consumption_id}",
            headers=authed_user.headers,
            json={"material_asset_id": material_id},
        )

        assert resp.status_code == 422


class TestDeleteConsumption:
    async def test_delete_restores_material_stock(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user)
        created = await _consume(
            client, authed_user, material_id=material_id, quantity="30", consumer_id=animal_id
        )
        consumption_id = created.json()["id"]  # type: ignore[attr-defined]

        resp = await client.delete(
            f"{_consumptions_url(authed_user.farm_id)}/{consumption_id}",
            headers=authed_user.headers,
        )

        assert resp.status_code == 204
        assert await _on_hand(client, authed_user, material_id) == "100"


class TestIdempotency:
    async def test_replay_returns_existing_record_without_duplicating(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user)
        first = await _consume(
            client,
            authed_user,
            material_id=material_id,
            consumer_id=animal_id,
            idempotency_key="feed-001",
        )
        second = await _consume(
            client,
            authed_user,
            material_id=material_id,
            consumer_id=animal_id,
            idempotency_key="feed-001",
        )

        assert first.status_code == 201  # type: ignore[attr-defined]
        assert second.status_code == 200  # type: ignore[attr-defined]
        assert first.json()["id"] == second.json()["id"]  # type: ignore[attr-defined]

    async def test_replay_does_not_decrement_stock_twice(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id, animal_id = await _setup(client, authed_user)
        for _ in range(2):
            await _consume(
                client,
                authed_user,
                material_id=material_id,
                quantity="30",
                consumer_id=animal_id,
                idempotency_key="feed-002",
            )

        assert await _on_hand(client, authed_user, material_id) == "70"
