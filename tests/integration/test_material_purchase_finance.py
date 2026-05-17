from decimal import Decimal

from httpx import AsyncClient

from tests.conftest import AuthedUser

MATERIAL = {"name": "Maíz", "kind": "material", "mode": "aggregated"}


def _assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def _purchases_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/material-purchases"


def _consumptions_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/material-consumptions"


async def _create_material(client: AsyncClient, authed: AuthedUser) -> int:
    resp = await client.post(_assets_url(authed.farm_id), headers=authed.headers, json=MATERIAL)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _purchase(
    client: AsyncClient,
    authed: AuthedUser,
    *,
    material_id: int,
    quantity: str = "100",
    amount: str = "40",
    occurred_at: str = "2026-04-10T10:00:00Z",
) -> dict:
    resp = await client.post(
        _purchases_url(authed.farm_id),
        headers=authed.headers,
        json={
            "material_asset_id": material_id,
            "occurred_at": occurred_at,
            "quantity": quantity,
            "unit": "kg",
            "amount": amount,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _consume_waste(
    client: AsyncClient, authed: AuthedUser, *, material_id: int, quantity: str
) -> None:
    resp = await client.post(
        _consumptions_url(authed.farm_id),
        headers=authed.headers,
        json={
            "material_asset_id": material_id,
            "occurred_at": "2026-04-20T10:00:00Z",
            "quantity": quantity,
            "unit": "kg",
            "reason": "waste",
        },
    )
    assert resp.status_code == 201, resp.text


async def _get_event(
    client: AsyncClient, authed: AuthedUser, material_id: int, event_id: int
) -> object:
    return await client.get(
        f"{_assets_url(authed.farm_id)}/{material_id}/events/{event_id}",
        headers=authed.headers,
    )


async def _on_hand_kg(client: AsyncClient, authed: AuthedUser, material_id: int) -> str | None:
    resp = await client.get(
        f"{_assets_url(authed.farm_id)}/{material_id}/events/balance",
        headers=authed.headers,
    )
    assert resp.status_code == 200, resp.text
    for row in resp.json()["balances"]:
        if row["unit"] == "kg":
            return str(row["on_hand"])
    return None


class TestExpenseLinkage:
    async def test_purchase_creates_a_linked_expense_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_material(client, authed_user)
        purchase = await _purchase(client, authed_user, material_id=material_id, amount="40")

        event = await _get_event(client, authed_user, material_id, purchase["expense_event_id"])

        assert event.status_code == 200, event.text  # type: ignore[attr-defined]
        body = event.json()  # type: ignore[attr-defined]
        assert body["type"] == "expense"
        assert Decimal(body["amount"]) == Decimal("40")

    async def test_update_amount_updates_the_expense_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_material(client, authed_user)
        purchase = await _purchase(client, authed_user, material_id=material_id, amount="40")

        await client.patch(
            f"{_purchases_url(authed_user.farm_id)}/{purchase['id']}",
            headers=authed_user.headers,
            json={"amount": "55"},
        )

        event = await _get_event(client, authed_user, material_id, purchase["expense_event_id"])
        assert Decimal(event.json()["amount"]) == Decimal("55")  # type: ignore[attr-defined]

    async def test_delete_removes_the_expense_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_material(client, authed_user)
        purchase = await _purchase(client, authed_user, material_id=material_id)

        await client.delete(
            f"{_purchases_url(authed_user.farm_id)}/{purchase['id']}",
            headers=authed_user.headers,
        )

        event = await _get_event(client, authed_user, material_id, purchase["expense_event_id"])
        assert event.status_code == 404  # type: ignore[attr-defined]


class TestExpenseReport:
    async def test_purchase_expense_appears_in_aggregate_report(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_material(client, authed_user)
        await _purchase(client, authed_user, material_id=material_id, amount="40")

        resp = await client.get(
            f"/api/v1/farms/{authed_user.farm_id}/reports/aggregate",
            headers=authed_user.headers,
            params={"type": "expense", "bucket": "day"},
        )

        assert resp.status_code == 200, resp.text
        rows = resp.json()["data"]
        assert sum(Decimal(r["value"]) for r in rows) == Decimal("40")


class TestPurchaseConsumptionInteraction:
    async def test_purchase_then_consumption_nets_to_correct_balance(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_material(client, authed_user)
        await _purchase(client, authed_user, material_id=material_id, quantity="100")

        await _consume_waste(client, authed_user, material_id=material_id, quantity="30")

        assert await _on_hand_kg(client, authed_user, material_id) == "70"

    async def test_edit_purchase_quantity_down_causing_oversell_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_material(client, authed_user)
        purchase = await _purchase(client, authed_user, material_id=material_id, quantity="100")
        await _consume_waste(client, authed_user, material_id=material_id, quantity="90")

        resp = await client.patch(
            f"{_purchases_url(authed_user.farm_id)}/{purchase['id']}",
            headers=authed_user.headers,
            json={"quantity": "50"},
        )

        assert resp.status_code == 409
        assert resp.json()["code"] == "insufficient_stock"

    async def test_delete_purchase_after_consumption_oversell_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_material(client, authed_user)
        purchase = await _purchase(client, authed_user, material_id=material_id, quantity="100")
        await _consume_waste(client, authed_user, material_id=material_id, quantity="90")

        resp = await client.delete(
            f"{_purchases_url(authed_user.farm_id)}/{purchase['id']}",
            headers=authed_user.headers,
        )

        assert resp.status_code == 409
