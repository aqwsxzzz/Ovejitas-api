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


async def _mortality_events(
    client: AsyncClient, authed: AuthedUser, asset_id: int, individual_id: int
) -> list[dict[str, object]]:
    resp = await client.get(
        events_url(authed.farm_id, asset_id),
        headers=authed.headers,
        params={"individual_id": individual_id, "type": "mortality"},
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


class TestMortalityEmission:
    async def test_transition_to_deceased_emits_mortality_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        individual_id = await _create_individual(client, authed_user, asset_id, "M-001")

        updated = await _patch(
            client,
            authed_user,
            asset_id,
            individual_id,
            {"status": "deceased", "died_at": "2026-05-10T00:00:00Z", "cause": "illness"},
        )

        assert updated.status_code == 200, updated.text
        assert updated.json()["mortality_event_id"] is not None
        events = await _mortality_events(client, authed_user, asset_id, individual_id)
        assert len(events) == 1
        assert events[0]["quantity"] == "1"
        assert events[0]["notes"] == "illness"
        assert events[0]["payload"]["source"] == "mortality"

    async def test_repeated_deceased_patch_emits_no_second_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        individual_id = await _create_individual(client, authed_user, asset_id, "M-002")
        await _patch(client, authed_user, asset_id, individual_id, {"status": "deceased"})

        await _patch(client, authed_user, asset_id, individual_id, {"status": "deceased"})

        events = await _mortality_events(client, authed_user, asset_id, individual_id)
        assert len(events) == 1

    async def test_died_at_without_deceased_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        individual_id = await _create_individual(client, authed_user, asset_id, "M-003")

        response = await _patch(
            client,
            authed_user,
            asset_id,
            individual_id,
            {"died_at": "2026-05-10T00:00:00Z"},
        )

        assert response.status_code == 422


class TestMortalityReconcileAndReverse:
    async def test_editing_died_at_moves_event_without_creating_new(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        individual_id = await _create_individual(client, authed_user, asset_id, "M-004")
        await _patch(
            client,
            authed_user,
            asset_id,
            individual_id,
            {"status": "deceased", "died_at": "2026-05-10T00:00:00Z"},
        )

        await _patch(
            client,
            authed_user,
            asset_id,
            individual_id,
            {"died_at": "2026-05-12T00:00:00Z"},
        )

        events = await _mortality_events(client, authed_user, asset_id, individual_id)
        assert len(events) == 1
        assert events[0]["occurred_at"].startswith("2026-05-12")

    async def test_transition_out_of_deceased_reverses_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        individual_id = await _create_individual(client, authed_user, asset_id, "M-005")
        await _patch(client, authed_user, asset_id, individual_id, {"status": "deceased"})

        updated = await _patch(client, authed_user, asset_id, individual_id, {"status": "active"})

        assert updated.status_code == 200, updated.text
        assert updated.json()["mortality_event_id"] is None
        assert await _mortality_events(client, authed_user, asset_id, individual_id) == []

    async def test_delete_deceased_individual_removes_mortality_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user)
        individual_id = await _create_individual(client, authed_user, asset_id, "M-006")
        await _patch(client, authed_user, asset_id, individual_id, {"status": "deceased"})

        delete = await client.delete(
            f"{individuals_url(authed_user.farm_id, asset_id)}/{individual_id}",
            headers=authed_user.headers,
        )

        assert delete.status_code == 204
        assert await _mortality_events(client, authed_user, asset_id, individual_id) == []
