from collections.abc import Awaitable, Callable

from httpx import AsyncClient

from tests.conftest import AuthedUser

ANIMAL_INDIVIDUAL = {"name": "Cattle", "kind": "animal", "mode": "individual"}
ANIMAL_AGGREGATED = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}
CROP_AGGREGATED = {"name": "Maize", "kind": "crop", "mode": "aggregated"}
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
    client: AsyncClient, authed: AuthedUser, event_type: str, name: str
) -> int:
    resp = await client.post(
        categories_url(authed.farm_id),
        headers=authed.headers,
        json={"type": event_type, "name": name},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class TestCreateByType:
    async def test_production(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)

        response = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "production",
                "occurred_at": OCCURRED,
                "quantity": "12.5",
                "unit": "liters",
            },
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["type"] == "production"
        assert body["quantity"] == "12.5"
        assert body["unit"] == "liters"
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
                "currency": "USD",
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

        response = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "production",
                "occurred_at": OCCURRED,
                "quantity": "5",
                "unit": "kg",
                "amount": "10",
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
                "currency": "USD",
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
                "currency": "USD",
                "category_id": feed,
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["category_id"] == feed


class TestIdempotency:
    async def test_same_key_rejected_on_farm(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        payload = {
            "type": "expense",
            "occurred_at": OCCURRED,
            "amount": "10.00",
            "currency": "USD",
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
        await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "production",
                "occurred_at": OCCURRED,
                "quantity": "5",
                "unit": "kg",
            },
        )
        await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "expense",
                "occurred_at": OCCURRED,
                "amount": "10",
                "currency": "USD",
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
