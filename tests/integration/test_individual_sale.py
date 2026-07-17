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


async def _create_individual(
    client: AsyncClient, authed: AuthedUser, asset_id: int, tag: str
) -> int:
    resp = await client.post(
        individuals_url(authed.farm_id, asset_id), headers=authed.headers, json={"tag": tag}
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


async def _patch(
    client: AsyncClient,
    authed: AuthedUser,
    asset_id: int,
    individual_id: int,
    body: dict[str, object],
) -> object:
    return await client.patch(
        f"{individuals_url(authed.farm_id, asset_id)}/{individual_id}",
        headers=authed.headers,
        json=body,
    )


class TestSaleEmission:
    async def test_transition_to_sold_emits_income_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        individual_id = await _create_individual(client, authed_user, asset_id, "S-001")

        updated = await _patch(
            client,
            authed_user,
            asset_id,
            individual_id,
            {"status": "sold", "sale_amount": "1200.00", "buyer": "Rancho Vecino"},
        )

        assert updated.status_code == 200, updated.text
        assert updated.json()["sale_event_id"] is not None
        events = await _events(client, authed_user, asset_id, individual_id, "income")
        assert len(events) == 1
        assert events[0]["amount"] == "1200.00"
        assert events[0]["currency_id"] is not None
        assert events[0]["payload"] == {"source": "sale", "buyer": "Rancho Vecino"}

    async def test_transition_to_sold_without_amount_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        individual_id = await _create_individual(client, authed_user, asset_id, "S-002")

        response = await _patch(client, authed_user, asset_id, individual_id, {"status": "sold"})

        assert response.status_code == 422

    async def test_repeated_sold_patch_emits_no_second_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        individual_id = await _create_individual(client, authed_user, asset_id, "S-003")
        await _patch(
            client,
            authed_user,
            asset_id,
            individual_id,
            {"status": "sold", "sale_amount": "500.00"},
        )

        await _patch(client, authed_user, asset_id, individual_id, {"status": "sold"})

        events = await _events(client, authed_user, asset_id, individual_id, "income")
        assert len(events) == 1

    async def test_sale_fields_without_sold_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        individual_id = await _create_individual(client, authed_user, asset_id, "S-004")

        response = await _patch(client, authed_user, asset_id, individual_id, {"buyer": "Someone"})

        assert response.status_code == 422


class TestSaleReconcileAndReverse:
    async def test_editing_sale_amount_moves_event_without_creating_new(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        individual_id = await _create_individual(client, authed_user, asset_id, "S-005")
        await _patch(
            client,
            authed_user,
            asset_id,
            individual_id,
            {"status": "sold", "sale_amount": "500.00"},
        )

        await _patch(client, authed_user, asset_id, individual_id, {"sale_amount": "650.00"})

        events = await _events(client, authed_user, asset_id, individual_id, "income")
        assert len(events) == 1
        assert events[0]["amount"] == "650.00"

    async def test_transition_out_of_sold_reverses_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        individual_id = await _create_individual(client, authed_user, asset_id, "S-006")
        await _patch(
            client,
            authed_user,
            asset_id,
            individual_id,
            {"status": "sold", "sale_amount": "500.00"},
        )

        updated = await _patch(client, authed_user, asset_id, individual_id, {"status": "active"})

        assert updated.status_code == 200, updated.text
        assert updated.json()["sale_event_id"] is None
        assert await _events(client, authed_user, asset_id, individual_id, "income") == []

    async def test_sold_to_deceased_reverses_income_and_emits_mortality(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        individual_id = await _create_individual(client, authed_user, asset_id, "S-007")
        await _patch(
            client,
            authed_user,
            asset_id,
            individual_id,
            {"status": "sold", "sale_amount": "500.00"},
        )

        await _patch(client, authed_user, asset_id, individual_id, {"status": "deceased"})

        assert await _events(client, authed_user, asset_id, individual_id, "income") == []
        assert len(await _events(client, authed_user, asset_id, individual_id, "mortality")) == 1

    async def test_delete_sold_individual_removes_income_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        individual_id = await _create_individual(client, authed_user, asset_id, "S-008")
        await _patch(
            client,
            authed_user,
            asset_id,
            individual_id,
            {"status": "sold", "sale_amount": "500.00"},
        )

        delete = await client.delete(
            f"{individuals_url(authed_user.farm_id, asset_id)}/{individual_id}",
            headers=authed_user.headers,
        )

        assert delete.status_code == 204
        assert await _events(client, authed_user, asset_id, individual_id, "income") == []
