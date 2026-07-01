from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient

from tests.conftest import AuthedUser

ANIMAL_INDIVIDUAL = {"name": "Cattle", "kind": "animal", "mode": "individual"}
ANIMAL_AGGREGATED = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}
CROP_AGGREGATED = {"name": "Maize", "kind": "crop", "mode": "aggregated"}
MATERIAL_AGGREGATED = {"name": "Maíz", "kind": "material", "mode": "aggregated"}
OCCURRED = "2026-04-20T10:00:00Z"


def assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def individuals_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/individuals"


def events_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/events"


def event_url(farm_id: int, asset_id: int, event_id: int) -> str:
    return f"{events_url(farm_id, asset_id)}/{event_id}"


def categories_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/event-categories"


async def _create_asset(client: AsyncClient, authed: AuthedUser, payload: dict) -> int:
    resp = await client.post(assets_url(authed.farm_id), headers=authed.headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_individual(
    client: AsyncClient, authed: AuthedUser, asset_id: int, name: str = "Vaca"
) -> int:
    resp = await client.post(
        individuals_url(authed.farm_id, asset_id),
        headers=authed.headers,
        json={"name": name, "tag": f"{name}-{asset_id}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_category(
    client: AsyncClient,
    authed: AuthedUser,
    event_type: str,
    name: str,
    unit: str | None = None,
) -> int:
    payload: dict[str, str] = {"type": event_type, "name": name}
    if unit is not None:
        payload["unit"] = unit
    resp = await client.post(
        categories_url(authed.farm_id),
        headers=authed.headers,
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class TestCreateByType:
    async def test_production(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        category_id = await _create_category(client, authed_user, "production", "Leche", "l")

        response = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "production",
                "occurred_at": OCCURRED,
                "quantity": "12.5",
                "unit": "l",
                "category_id": category_id,
            },
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["type"] == "production"
        assert body["quantity"] == "12.5"
        assert body["unit"] == "l"
        assert body["amount"] is None

    async def test_expense_requires_amount(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)

        response = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"type": "expense", "occurred_at": OCCURRED},
        )
        assert response.status_code == 422

    async def test_expense_ok(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)

        response = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "expense",
                "occurred_at": OCCURRED,
                "amount": "100.00",
            },
        )
        assert response.status_code == 201
        assert response.json()["amount"] == "100.00"

    async def test_observation(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)

        response = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"type": "observation", "occurred_at": OCCURRED, "notes": "Looks healthy"},
        )
        assert response.status_code == 201

    async def test_production_rejects_extra_amount(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        category_id = await _create_category(client, authed_user, "production", "Lana", "kg")

        response = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "production",
                "occurred_at": OCCURRED,
                "quantity": "5",
                "unit": "kg",
                "amount": "10",
                "category_id": category_id,
            },
        )
        assert response.status_code == 422


class TestGuards:
    async def test_reproductive_needs_animal_kind(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, CROP_AGGREGATED)

        response = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "reproductive",
                "occurred_at": OCCURRED,
                "individual_id": 1,
            },
        )
        assert response.status_code == 422
        assert "animal" in response.json()["detail"].lower()

    async def test_reproductive_happy_path(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        individual_id = await _create_individual(client, authed_user, asset_id)

        response = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "reproductive",
                "occurred_at": OCCURRED,
                "individual_id": individual_id,
                "payload": {"outcome": "pregnant"},
            },
        )
        assert response.status_code == 201, response.text

    async def test_individual_on_aggregated_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        aggregated = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        individual_asset = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        individual_id = await _create_individual(client, authed_user, individual_asset)

        response = await client.post(
            events_url(authed_user.farm_id, aggregated),
            headers=authed_user.headers,
            json={
                "type": "observation",
                "occurred_at": OCCURRED,
                "individual_id": individual_id,
            },
        )
        assert response.status_code == 422
        assert "aggregated" in response.json()["detail"].lower()

    async def test_individual_must_belong_to_asset(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_a = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        asset_b = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        individual_in_b = await _create_individual(client, authed_user, asset_b, name="Cow B")

        response = await client.post(
            events_url(authed_user.farm_id, asset_a),
            headers=authed_user.headers,
            json={
                "type": "observation",
                "occurred_at": OCCURRED,
                "individual_id": individual_in_b,
            },
        )
        assert response.status_code == 422
        assert "belong" in response.json()["detail"].lower()

    async def test_category_type_must_match(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        income_category = await _create_category(client, authed_user, "income", "Sale")

        response = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "expense",
                "occurred_at": OCCURRED,
                "amount": "100.00",
                "category_id": income_category,
            },
        )
        assert response.status_code == 422
        assert "category" in response.json()["detail"].lower()

    async def test_category_matches(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        feed = await _create_category(client, authed_user, "expense", "Feed")

        response = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "expense",
                "occurred_at": OCCURRED,
                "amount": "50.00",
                "category_id": feed,
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["category_id"] == feed

    async def test_production_requires_category(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)

        response = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"type": "production", "occurred_at": OCCURRED, "quantity": "5", "unit": "kg"},
        )
        assert response.status_code == 422

    async def test_production_unit_must_match_category_family(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        eggs = await _create_category(client, authed_user, "production", "Huevos", "unit")

        response = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "production",
                "occurred_at": OCCURRED,
                "quantity": "5",
                "unit": "kg",
                "category_id": eggs,
            },
        )
        assert response.status_code == 422
        assert "compatible" in response.json()["detail"].lower()

    async def test_production_category_cannot_be_nulled(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        category_id = await _create_category(client, authed_user, "production", "Lana", "kg")
        created = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "production",
                "occurred_at": OCCURRED,
                "quantity": "5",
                "unit": "kg",
                "category_id": category_id,
            },
        )
        event_id = created.json()["id"]

        response = await client.patch(
            event_url(authed_user.farm_id, asset_id, event_id),
            headers=authed_user.headers,
            json={"category_id": None},
        )
        assert response.status_code == 422


class TestIdempotency:
    async def test_same_key_rejected_on_farm(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        payload = {
            "type": "expense",
            "occurred_at": OCCURRED,
            "amount": "10.00",
            "idempotency_key": "key-1",
        }

        first = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json=payload,
        )
        assert first.status_code == 201

        duplicate = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json=payload,
        )
        assert duplicate.status_code == 409


class TestListAndUpdate:
    async def test_filter_by_type(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        category_id = await _create_category(client, authed_user, "production", "Lana", "kg")
        await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "production",
                "occurred_at": OCCURRED,
                "quantity": "5",
                "unit": "kg",
                "category_id": category_id,
            },
        )
        await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "expense",
                "occurred_at": OCCURRED,
                "amount": "10",
            },
        )

        response = await client.get(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            params={"type": "expense"},
        )
        assert response.json()["meta"]["total"] == 1

    async def test_update_notes(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        created = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"type": "observation", "occurred_at": OCCURRED, "notes": "old"},
        )
        event_id = created.json()["id"]

        response = await client.patch(
            event_url(authed_user.farm_id, asset_id, event_id),
            headers=authed_user.headers,
            json={"notes": "updated"},
        )
        assert response.status_code == 200
        assert response.json()["notes"] == "updated"

    async def test_delete(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        created = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"type": "observation", "occurred_at": OCCURRED},
        )
        event_id = created.json()["id"]

        delete = await client.delete(
            event_url(authed_user.farm_id, asset_id, event_id),
            headers=authed_user.headers,
        )
        assert delete.status_code == 204

        follow_up = await client.get(
            event_url(authed_user.farm_id, asset_id, event_id),
            headers=authed_user.headers,
        )
        assert follow_up.status_code == 404


class TestFarmScope:
    async def test_non_member_forbidden(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("alice@example.com")
        bob = await register_user("bob@example.com")
        alice_asset = await _create_asset(client, alice, ANIMAL_AGGREGATED)

        response = await client.get(
            events_url(alice.farm_id, alice_asset),
            headers=bob.headers,
        )
        assert response.status_code == 403


class TestActionOwnedTypesRejected:
    """ACQUISITION and MORTALITY events are owned by individual lifecycle
    actions and must not be hand-written via POST /events (Philosophy 1)."""

    @pytest.mark.parametrize("event_type", ["acquisition", "mortality"])
    async def test_action_owned_type_rejected(
        self, client: AsyncClient, authed_user: AuthedUser, event_type: str
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)

        response = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"type": event_type, "occurred_at": OCCURRED, "quantity": "1"},
        )

        assert response.status_code == 422


def _flock_url(farm_id: int, asset_id: int, action: str) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/flock/{action}"


def _inventory_event(adjustment: str, quantity: str) -> dict[str, str]:
    return {
        "type": "inventory",
        "occurred_at": OCCURRED,
        "adjustment": adjustment,
        "quantity": quantity,
        "unit": "kg",
    }


class TestEventWritePathGuards:
    """POST/PATCH/DELETE /events must respect the action layer's invariants —
    the stock guard and action-owned-event immutability (Philosophy 1)."""

    async def test_manual_inventory_decrement_cannot_oversell(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL_AGGREGATED)
        inc = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json=_inventory_event("increment", "10"),
        )
        assert inc.status_code == 201, inc.text

        dec = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json=_inventory_event("decrement", "50"),
        )
        assert dec.status_code == 409

    async def test_cannot_edit_action_owned_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        acq = await client.post(
            _flock_url(authed_user.farm_id, asset_id, "acquisitions"),
            headers=authed_user.headers,
            json={"quantity": 10},
        )
        assert acq.status_code == 201, acq.text
        listed = await client.get(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            params={"type": "inventory"},
        )
        event_id = listed.json()["data"][0]["id"]

        resp = await client.patch(
            event_url(authed_user.farm_id, asset_id, event_id),
            headers=authed_user.headers,
            json={"notes": "tampered"},
        )
        assert resp.status_code == 422

    async def test_cannot_delete_action_owned_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        acq = await client.post(
            _flock_url(authed_user.farm_id, asset_id, "acquisitions"),
            headers=authed_user.headers,
            json={"quantity": 10},
        )
        assert acq.status_code == 201, acq.text
        listed = await client.get(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            params={"type": "inventory"},
        )
        event_id = listed.json()["data"][0]["id"]

        resp = await client.delete(
            event_url(authed_user.farm_id, asset_id, event_id),
            headers=authed_user.headers,
        )
        assert resp.status_code == 422

    async def test_update_rejects_field_not_valid_for_type(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        category_id = await _create_category(client, authed_user, "production", "Lana", "kg")
        created = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "production",
                "occurred_at": OCCURRED,
                "quantity": "5",
                "unit": "kg",
                "category_id": category_id,
            },
        )
        event_id = created.json()["id"]

        resp = await client.patch(
            event_url(authed_user.farm_id, asset_id, event_id),
            headers=authed_user.headers,
            json={"amount": "9"},
        )
        assert resp.status_code == 422

    async def test_deleting_inventory_increment_guards_negative_stock(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL_AGGREGATED)
        inc = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json=_inventory_event("increment", "10"),
        )
        increment_id = inc.json()["id"]
        await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json=_inventory_event("decrement", "8"),
        )

        resp = await client.delete(
            event_url(authed_user.farm_id, asset_id, increment_id),
            headers=authed_user.headers,
        )
        assert resp.status_code == 409

    async def test_editing_inventory_event_guards_negative_stock(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL_AGGREGATED)
        inc = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json=_inventory_event("increment", "10"),
        )
        increment_id = inc.json()["id"]
        await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json=_inventory_event("decrement", "8"),
        )

        # lowering the increment from 10 to 5 leaves 5 - 8 = -3 on hand
        resp = await client.patch(
            event_url(authed_user.farm_id, asset_id, increment_id),
            headers=authed_user.headers,
            json={"quantity": "5"},
        )
        assert resp.status_code == 409

    async def test_manual_create_rejects_reserved_source(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)

        resp = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "observation",
                "occurred_at": OCCURRED,
                "payload": {"source": "harvest"},
            },
        )
        assert resp.status_code == 422
