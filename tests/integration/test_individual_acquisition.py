from httpx import AsyncClient

from tests.conftest import AuthedUser

ANIMAL_INDIVIDUAL = {"name": "Cattle", "kind": "animal", "mode": "individual"}


def assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def individuals_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/individuals"


def events_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/events"


async def _create_asset(client: AsyncClient, authed: AuthedUser) -> int:
    resp = await client.post(
        assets_url(authed.farm_id), headers=authed.headers, json=ANIMAL_INDIVIDUAL
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _events(
    client: AsyncClient, authed: AuthedUser, asset_id: int, individual_id: int, event_type: str
) -> list[dict[str, object]]:
    resp = await client.get(
        events_url(authed.farm_id, asset_id),
        headers=authed.headers,
        params={"individual_id": individual_id, "type": event_type},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


class TestCreateAcquisition:
    async def test_create_emits_one_acquisition_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)

        created = await client.post(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"tag": "A-001"},
        )

        assert created.status_code == 201, created.text
        individual_id = created.json()["id"]
        assert created.json()["acquisition_event_id"] is not None
        assert created.json()["acquisition_expense_event_id"] is None
        events = await _events(client, authed_user, asset_id, individual_id, "acquisition")
        assert len(events) == 1
        assert events[0]["payload"]["method"] == "other"

    async def test_purchased_create_emits_paired_expense_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)

        created = await client.post(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"tag": "A-002", "acquisition_method": "purchased", "amount": "1500.00"},
        )

        assert created.status_code == 201, created.text
        individual_id = created.json()["id"]
        assert created.json()["acquisition_expense_event_id"] is not None
        expenses = await _events(client, authed_user, asset_id, individual_id, "expense")
        assert len(expenses) == 1
        assert expenses[0]["amount"] == "1500.00"
        assert expenses[0]["currency"] == "USD"

    async def test_purchased_without_amount_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)

        response = await client.post(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"tag": "A-003", "acquisition_method": "purchased"},
        )

        assert response.status_code == 422

    async def test_amount_without_purchased_method_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)

        response = await client.post(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"tag": "A-004", "acquisition_method": "born", "amount": "200.00"},
        )

        assert response.status_code == 422


class TestUpdateAcquisition:
    async def test_changing_method_to_purchased_creates_expense(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        created = await client.post(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"tag": "A-005", "acquisition_method": "born"},
        )
        individual_id = created.json()["id"]

        updated = await client.patch(
            f"{individuals_url(authed_user.farm_id, asset_id)}/{individual_id}",
            headers=authed_user.headers,
            json={"acquisition_method": "purchased", "amount": "900.00"},
        )

        assert updated.status_code == 200, updated.text
        assert updated.json()["acquisition_expense_event_id"] is not None
        expenses = await _events(client, authed_user, asset_id, individual_id, "expense")
        assert len(expenses) == 1
        assert expenses[0]["amount"] == "900.00"

    async def test_changing_method_away_from_purchased_deletes_expense(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        created = await client.post(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"tag": "A-006", "acquisition_method": "purchased", "amount": "500.00"},
        )
        individual_id = created.json()["id"]

        updated = await client.patch(
            f"{individuals_url(authed_user.farm_id, asset_id)}/{individual_id}",
            headers=authed_user.headers,
            json={"acquisition_method": "born"},
        )

        assert updated.status_code == 200, updated.text
        assert updated.json()["acquisition_expense_event_id"] is None
        expenses = await _events(client, authed_user, asset_id, individual_id, "expense")
        assert expenses == []

    async def test_updating_amount_reconciles_expense(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        created = await client.post(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"tag": "A-007", "acquisition_method": "purchased", "amount": "500.00"},
        )
        individual_id = created.json()["id"]

        await client.patch(
            f"{individuals_url(authed_user.farm_id, asset_id)}/{individual_id}",
            headers=authed_user.headers,
            json={"amount": "750.00"},
        )

        expenses = await _events(client, authed_user, asset_id, individual_id, "expense")
        assert len(expenses) == 1
        assert expenses[0]["amount"] == "750.00"


class TestDeleteAcquisition:
    async def test_delete_removes_acquisition_and_expense_events(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        created = await client.post(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"tag": "A-008", "acquisition_method": "purchased", "amount": "300.00"},
        )
        individual_id = created.json()["id"]

        delete = await client.delete(
            f"{individuals_url(authed_user.farm_id, asset_id)}/{individual_id}",
            headers=authed_user.headers,
        )

        assert delete.status_code == 204
        assert await _events(client, authed_user, asset_id, individual_id, "acquisition") == []
        assert await _events(client, authed_user, asset_id, individual_id, "expense") == []
