from httpx import AsyncClient

from tests.conftest import AuthedUser

ANIMAL_FLOCK = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}
CROP_FIELD = {"name": "Tomateras", "kind": "crop", "mode": "aggregated"}
EQUIPMENT = {"name": "Tractor", "kind": "equipment", "mode": "individual"}
EGGS = {"name": "Huevos", "kind": "material", "mode": "aggregated"}


def assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def harvest_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/harvests"


def events_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/events"


async def _create_asset(client: AsyncClient, authed: AuthedUser, body: dict[str, str]) -> int:
    resp = await client.post(assets_url(authed.farm_id), headers=authed.headers, json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _link_produce(
    client: AsyncClient, authed: AuthedUser, source_id: int, produce_id: int
) -> object:
    return await client.patch(
        f"{assets_url(authed.farm_id)}/{source_id}",
        headers=authed.headers,
        json={"produce_asset_id": produce_id},
    )


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


async def _linked_source(
    client: AsyncClient, authed: AuthedUser, source_body: dict[str, str]
) -> tuple[int, int]:
    """Create a source asset linked to a fresh 'Huevos' produce asset."""
    produce_id = await _create_asset(client, authed, EGGS)
    source_id = await _create_asset(client, authed, source_body)
    linked = await _link_produce(client, authed, source_id, produce_id)
    assert linked.status_code == 200, linked.text
    return source_id, produce_id


class TestHarvest:
    async def test_harvest_emits_production_and_increments_stock(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        source_id, produce_id = await _linked_source(client, authed_user, ANIMAL_FLOCK)

        resp = await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={"quantity": "15", "unit": "unit"},
        )

        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["produce_balance"] == "15"
        production = await _events(client, authed_user, source_id, "production")
        assert len(production) == 1
        assert production[0]["id"] == body["production_event_id"]
        increments = await _events(client, authed_user, produce_id, "inventory")
        assert len(increments) == 1
        assert increments[0]["id"] == body["inventory_event_id"]

    async def test_events_carry_correct_asset_ids(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        source_id, produce_id = await _linked_source(client, authed_user, ANIMAL_FLOCK)

        await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={"quantity": "15", "unit": "unit"},
        )

        production = await _events(client, authed_user, source_id, "production")
        increments = await _events(client, authed_user, produce_id, "inventory")
        assert production[0]["asset_id"] == source_id
        assert increments[0]["asset_id"] == produce_id

    async def test_two_flocks_pool_into_one_produce_balance(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        produce_id = await _create_asset(client, authed_user, EGGS)
        flock_a = await _create_asset(client, authed_user, ANIMAL_FLOCK)
        flock_b = await _create_asset(client, authed_user, ANIMAL_FLOCK)
        await _link_produce(client, authed_user, flock_a, produce_id)
        await _link_produce(client, authed_user, flock_b, produce_id)

        await client.post(
            harvest_url(authed_user.farm_id, flock_a),
            headers=authed_user.headers,
            json={"quantity": "10", "unit": "unit"},
        )
        resp = await client.post(
            harvest_url(authed_user.farm_id, flock_b),
            headers=authed_user.headers,
            json={"quantity": "7", "unit": "unit"},
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["produce_balance"] == "17"

    async def test_harvest_from_crop_asset(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        source_id, _ = await _linked_source(client, authed_user, CROP_FIELD)

        resp = await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={"quantity": "40", "unit": "kg"},
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["produce_balance"] == "40"


class TestHarvestRejections:
    async def test_harvest_from_unlinked_asset_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        source_id = await _create_asset(client, authed_user, ANIMAL_FLOCK)

        resp = await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={"quantity": "15", "unit": "unit"},
        )

        assert resp.status_code == 422

    async def test_unit_must_match_produce_stock(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        source_id, _ = await _linked_source(client, authed_user, ANIMAL_FLOCK)
        await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={"quantity": "15", "unit": "unit"},
        )

        resp = await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={"quantity": "1", "unit": "dozen"},
        )

        assert resp.status_code == 422

    async def test_zero_quantity_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        source_id, _ = await _linked_source(client, authed_user, ANIMAL_FLOCK)

        resp = await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={"quantity": "0", "unit": "unit"},
        )

        assert resp.status_code == 422


class TestProduceLinkValidation:
    async def test_link_to_non_material_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock = await _create_asset(client, authed_user, ANIMAL_FLOCK)
        other_flock = await _create_asset(client, authed_user, ANIMAL_FLOCK)

        resp = await _link_produce(client, authed_user, flock, other_flock)

        assert resp.status_code == 422

    async def test_link_on_equipment_asset_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        equipment = await _create_asset(client, authed_user, EQUIPMENT)
        produce = await _create_asset(client, authed_user, EGGS)

        resp = await _link_produce(client, authed_user, equipment, produce)

        assert resp.status_code == 422
