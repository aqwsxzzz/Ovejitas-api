from httpx import AsyncClient

from tests.conftest import AuthedUser

MATERIAL = {"name": "Maíz", "kind": "material", "mode": "aggregated"}
ANIMAL = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}


def _assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def _purchases_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/material-purchases"


def _balance_url(farm_id: int, asset_id: int) -> str:
    return f"{_assets_url(farm_id)}/{asset_id}/events/balance"


async def _create_asset(client: AsyncClient, authed: AuthedUser, payload: dict) -> int:
    resp = await client.post(_assets_url(authed.farm_id), headers=authed.headers, json=payload)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _on_hand(
    client: AsyncClient, authed: AuthedUser, asset_id: int, unit: str = "kg"
) -> str | None:
    resp = await client.get(_balance_url(authed.farm_id, asset_id), headers=authed.headers)
    assert resp.status_code == 200, resp.text
    for row in resp.json()["balances"]:
        if row["unit"] == unit:
            return str(row["on_hand"])
    return None


async def _purchase(
    client: AsyncClient,
    authed: AuthedUser,
    *,
    material_id: int,
    quantity: str = "50",
    unit: str = "kg",
    amount: str = "40",
    occurred_at: str = "2026-04-20T10:00:00Z",
    idempotency_key: str | None = None,
) -> object:
    payload: dict = {
        "material_asset_id": material_id,
        "occurred_at": occurred_at,
        "quantity": quantity,
        "unit": unit,
        "amount": amount,
    }
    if idempotency_key is not None:
        payload["idempotency_key"] = idempotency_key
    return await client.post(_purchases_url(authed.farm_id), headers=authed.headers, json=payload)


class TestCreatePurchase:
    async def test_create_raises_material_stock(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_asset(client, authed_user, MATERIAL)

        resp = await _purchase(client, authed_user, material_id=material_id, quantity="50")

        assert resp.status_code == 201, resp.text
        assert await _on_hand(client, authed_user, material_id) == "50"

    async def test_first_purchase_establishes_any_unit(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_asset(client, authed_user, MATERIAL)

        resp = await _purchase(client, authed_user, material_id=material_id, unit="t")

        assert resp.status_code == 201, resp.text

    async def test_purchase_in_conflicting_unit_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_asset(client, authed_user, MATERIAL)
        await _purchase(client, authed_user, material_id=material_id, unit="kg")

        resp = await _purchase(client, authed_user, material_id=material_id, unit="l")

        assert resp.status_code == 422

    async def test_amount_must_be_positive(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_asset(client, authed_user, MATERIAL)

        resp = await _purchase(client, authed_user, material_id=material_id, amount="0")

        assert resp.status_code == 422

    async def test_material_must_be_a_material_asset(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        animal_id = await _create_asset(client, authed_user, ANIMAL)

        resp = await _purchase(client, authed_user, material_id=animal_id)

        assert resp.status_code == 422

    async def test_material_from_another_farm_is_rejected(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: object,
    ) -> None:
        other = await register_user("other@example.com")  # type: ignore[operator]
        other_material = await _create_asset(client, other, MATERIAL)

        resp = await _purchase(client, authed_user, material_id=other_material)

        assert resp.status_code in (403, 404)


class TestUpdatePurchase:
    async def test_update_quantity_reconciles_stock(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_asset(client, authed_user, MATERIAL)
        created = await _purchase(client, authed_user, material_id=material_id, quantity="50")
        purchase_id = created.json()["id"]  # type: ignore[attr-defined]

        resp = await client.patch(
            f"{_purchases_url(authed_user.farm_id)}/{purchase_id}",
            headers=authed_user.headers,
            json={"quantity": "80"},
        )

        assert resp.status_code == 200, resp.text
        assert await _on_hand(client, authed_user, material_id) == "80"

    async def test_material_asset_id_is_immutable(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_asset(client, authed_user, MATERIAL)
        created = await _purchase(client, authed_user, material_id=material_id)
        purchase_id = created.json()["id"]  # type: ignore[attr-defined]

        resp = await client.patch(
            f"{_purchases_url(authed_user.farm_id)}/{purchase_id}",
            headers=authed_user.headers,
            json={"material_asset_id": material_id},
        )

        assert resp.status_code == 422


class TestDeletePurchase:
    async def test_delete_reverses_the_stock_increment(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_asset(client, authed_user, MATERIAL)
        created = await _purchase(client, authed_user, material_id=material_id, quantity="50")
        purchase_id = created.json()["id"]  # type: ignore[attr-defined]

        resp = await client.delete(
            f"{_purchases_url(authed_user.farm_id)}/{purchase_id}",
            headers=authed_user.headers,
        )

        assert resp.status_code == 204
        assert await _on_hand(client, authed_user, material_id) is None


class TestIdempotency:
    async def test_replay_returns_existing_record(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_asset(client, authed_user, MATERIAL)
        first = await _purchase(
            client, authed_user, material_id=material_id, idempotency_key="buy-001"
        )
        second = await _purchase(
            client, authed_user, material_id=material_id, idempotency_key="buy-001"
        )

        assert first.status_code == 201  # type: ignore[attr-defined]
        assert second.status_code == 200  # type: ignore[attr-defined]
        assert first.json()["id"] == second.json()["id"]  # type: ignore[attr-defined]

    async def test_replay_does_not_increment_stock_twice(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_asset(client, authed_user, MATERIAL)
        for _ in range(2):
            await _purchase(
                client,
                authed_user,
                material_id=material_id,
                quantity="50",
                idempotency_key="buy-002",
            )

        assert await _on_hand(client, authed_user, material_id) == "50"
