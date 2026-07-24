from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError
from ovejitas.features.asset.models import AssetKind, AssetMode
from ovejitas.features.event.types import Unit
from ovejitas.features.harvest.actions import create_harvest
from ovejitas.features.harvest.schemas import HarvestCreate
from tests.conftest import AuthedUser
from tests.factories import AssetFactory, EventCategoryFactory, FarmFactory, UserFactory

ANIMAL_FLOCK = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}
CROP_FIELD = {"name": "Tomateras", "kind": "crop", "mode": "aggregated"}
EQUIPMENT = {"name": "Tractor", "kind": "equipment", "mode": "individual"}
EGGS = {"name": "Huevos", "kind": "produce", "mode": "aggregated"}
FEED = {"name": "Maíz", "kind": "material", "mode": "aggregated"}


def assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def harvest_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/harvests"


def events_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/events"


def categories_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/event-categories"


async def _create_asset(client: AsyncClient, authed: AuthedUser, body: dict[str, str]) -> int:
    resp = await client.post(assets_url(authed.farm_id), headers=authed.headers, json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _prod_category(client: AsyncClient, authed: AuthedUser, unit: str) -> int:
    """A production category (the harvest's product) whose unit family matches the
    harvested unit."""
    resp = await client.post(
        categories_url(authed.farm_id),
        headers=authed.headers,
        json={"type": "production", "name": f"Producción {unit}", "unit": unit},
    )
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
        category_id = await _prod_category(client, authed_user, "unit")

        resp = await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={
                "quantity": "15",
                "unit": "unit",
                "produce_asset_id": produce_id,
                "category_id": category_id,
            },
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
        category_id = await _prod_category(client, authed_user, "unit")

        await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={
                "quantity": "15",
                "unit": "unit",
                "produce_asset_id": produce_id,
                "category_id": category_id,
            },
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
        category_id = await _prod_category(client, authed_user, "unit")

        await client.post(
            harvest_url(authed_user.farm_id, flock_a),
            headers=authed_user.headers,
            json={
                "quantity": "10",
                "unit": "unit",
                "produce_asset_id": produce_id,
                "category_id": category_id,
            },
        )
        resp = await client.post(
            harvest_url(authed_user.farm_id, flock_b),
            headers=authed_user.headers,
            json={
                "quantity": "7",
                "unit": "unit",
                "produce_asset_id": produce_id,
                "category_id": category_id,
            },
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["produce_balance"] == "17"

    async def test_harvest_from_crop_asset(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        source_id, produce_id = await _linked_source(client, authed_user, CROP_FIELD)
        category_id = await _prod_category(client, authed_user, "kg")

        resp = await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={
                "quantity": "40",
                "unit": "kg",
                "produce_asset_id": produce_id,
                "category_id": category_id,
            },
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["produce_balance"] == "40"


class TestHarvestDestination:
    async def test_harvest_without_produce_asset_id_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        source_id, _ = await _linked_source(client, authed_user, ANIMAL_FLOCK)
        category_id = await _prod_category(client, authed_user, "unit")

        resp = await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={"quantity": "15", "unit": "unit", "category_id": category_id},
        )

        assert resp.status_code == 422

    async def test_harvest_from_unlinked_asset_succeeds_when_destination_named(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        # asset.produce_asset_id is only a UI default now — the request names
        # the destination, so an unlinked producer harvests fine.
        produce_id = await _create_asset(client, authed_user, EGGS)
        source_id = await _create_asset(client, authed_user, ANIMAL_FLOCK)
        category_id = await _prod_category(client, authed_user, "unit")

        resp = await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={
                "quantity": "15",
                "unit": "unit",
                "produce_asset_id": produce_id,
                "category_id": category_id,
            },
        )

        assert resp.status_code == 201, resp.text

    async def test_one_producer_can_harvest_into_two_pools(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        eggs_id = await _create_asset(client, authed_user, EGGS)
        feathers_id = await _create_asset(client, authed_user, {**EGGS, "name": "Plumas"})
        source_id = await _create_asset(client, authed_user, ANIMAL_FLOCK)
        category_id = await _prod_category(client, authed_user, "unit")

        for pool_id, quantity in ((eggs_id, "15"), (feathers_id, "4")):
            resp = await client.post(
                harvest_url(authed_user.farm_id, source_id),
                headers=authed_user.headers,
                json={
                    "quantity": quantity,
                    "unit": "unit",
                    "produce_asset_id": pool_id,
                    "category_id": category_id,
                },
            )
            assert resp.status_code == 201, resp.text

        assert len(await _events(client, authed_user, eggs_id, "inventory")) == 1
        assert len(await _events(client, authed_user, feathers_id, "inventory")) == 1

    async def test_harvest_into_animal_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        source_id = await _create_asset(client, authed_user, ANIMAL_FLOCK)
        other_flock = await _create_asset(client, authed_user, ANIMAL_FLOCK)
        category_id = await _prod_category(client, authed_user, "unit")

        resp = await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={
                "quantity": "15",
                "unit": "unit",
                "produce_asset_id": other_flock,
                "category_id": category_id,
            },
        )

        assert resp.status_code == 422

    async def test_harvest_into_consumable_material_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        # The bug this feature fixes: a consumable material (feed) is no longer a
        # valid harvest destination — only produce pools are.
        source_id = await _create_asset(client, authed_user, ANIMAL_FLOCK)
        feed_id = await _create_asset(client, authed_user, FEED)
        category_id = await _prod_category(client, authed_user, "unit")

        resp = await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={
                "quantity": "15",
                "unit": "unit",
                "produce_asset_id": feed_id,
                "category_id": category_id,
            },
        )

        assert resp.status_code == 422


class TestHarvestRejections:
    async def test_unit_must_match_produce_stock(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        source_id, produce_id = await _linked_source(client, authed_user, ANIMAL_FLOCK)
        category_id = await _prod_category(client, authed_user, "unit")
        await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={
                "quantity": "15",
                "unit": "unit",
                "produce_asset_id": produce_id,
                "category_id": category_id,
            },
        )

        resp = await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={
                "quantity": "1",
                "unit": "dozen",
                "produce_asset_id": produce_id,
                "category_id": category_id,
            },
        )

        assert resp.status_code == 422

    async def test_zero_quantity_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        source_id, produce_id = await _linked_source(client, authed_user, ANIMAL_FLOCK)
        category_id = await _prod_category(client, authed_user, "unit")

        resp = await client.post(
            harvest_url(authed_user.farm_id, source_id),
            headers=authed_user.headers,
            json={
                "quantity": "0",
                "unit": "unit",
                "produce_asset_id": produce_id,
                "category_id": category_id,
            },
        )

        assert resp.status_code == 422


class TestProduceLinkValidation:
    async def test_link_to_animal_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock = await _create_asset(client, authed_user, ANIMAL_FLOCK)
        other_flock = await _create_asset(client, authed_user, ANIMAL_FLOCK)

        resp = await _link_produce(client, authed_user, flock, other_flock)

        assert resp.status_code == 422

    async def test_link_to_consumable_material_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        # A producer's produce target must be a produce pool, not a consumable.
        flock = await _create_asset(client, authed_user, ANIMAL_FLOCK)
        feed = await _create_asset(client, authed_user, FEED)

        resp = await _link_produce(client, authed_user, flock, feed)

        assert resp.status_code == 422

    async def test_link_on_equipment_asset_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        equipment = await _create_asset(client, authed_user, EQUIPMENT)
        produce = await _create_asset(client, authed_user, EGGS)

        resp = await _link_produce(client, authed_user, equipment, produce)

        assert resp.status_code == 422


class TestHarvestCrossFarmGuard:
    async def test_harvest_rejects_produce_asset_in_another_farm(
        self, db_session: AsyncSession
    ) -> None:
        # The destination id now comes from the request, so this is the
        # authorization boundary, not just defence in depth: naming another
        # farm's pool must not deposit into it, nor confirm that it exists.
        farm_a = await FarmFactory.create_async()
        farm_b = await FarmFactory.create_async()
        produce = await AssetFactory.create_async(
            farm_id=farm_b.id, kind=AssetKind.PRODUCE, mode=AssetMode.AGGREGATED
        )
        source = await AssetFactory.create_async(
            farm_id=farm_a.id,
            kind=AssetKind.ANIMAL,
            mode=AssetMode.AGGREGATED,
        )
        user = await UserFactory.create_async()
        category = await EventCategoryFactory.create_async(farm_id=farm_a.id, unit=Unit.UNIT)

        with pytest.raises(NotFoundError, match="not found in this farm"):
            await create_harvest(
                db_session,
                asset=source,
                user_id=user.id,
                data=HarvestCreate(
                    quantity=Decimal("5"),
                    unit=Unit.UNIT,
                    produce_asset_id=produce.id,
                    category_id=category.id,
                ),
            )
