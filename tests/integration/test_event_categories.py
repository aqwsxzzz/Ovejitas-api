from collections.abc import Awaitable, Callable

from httpx import AsyncClient

from tests.conftest import AuthedUser


def categories_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/event-categories"


def category_url(farm_id: int, category_id: int) -> str:
    return f"{categories_url(farm_id)}/{category_id}"


class TestCreateEventCategory:
    async def test_creates_category(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        response = await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"type": "expense", "name": "Feed", "color": "#ff0000"},
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["type"] == "expense"
        assert body["name"] == "Feed"
        assert body["color"] == "#ff0000"
        assert body["archived_at"] is None

    async def test_create_category_with_unit_persists_and_returns_unit(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        response = await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"type": "production", "name": "Huevos", "unit": "unit"},
        )

        assert response.status_code == 201, response.text
        assert response.json()["unit"] == "unit"

    async def test_production_category_without_unit_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        response = await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"type": "production", "name": "Huevos"},
        )

        assert response.status_code == 422

    async def test_non_production_category_with_unit_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        response = await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"type": "expense", "name": "Feed", "unit": "kg"},
        )

        assert response.status_code == 422

    async def test_duplicate_rejected(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        payload = {"type": "expense", "name": "Feed"}
        first = await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=payload,
        )
        assert first.status_code == 201

        duplicate = await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=payload,
        )
        assert duplicate.status_code == 409

    async def test_same_name_different_type_allowed(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        for event_type in ["expense", "income"]:
            resp = await client.post(
                categories_url(authed_user.farm_id),
                headers=authed_user.headers,
                json={"type": event_type, "name": "Misc"},
            )
            assert resp.status_code == 201


class TestListEventCategories:
    async def test_filter_by_type(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        for event_type, name in [
            ("expense", "Feed"),
            ("expense", "Vet"),
            ("income", "Sale"),
        ]:
            await client.post(
                categories_url(authed_user.farm_id),
                headers=authed_user.headers,
                json={"type": event_type, "name": name},
            )

        response = await client.get(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"type": "expense"},
        )

        body = response.json()
        assert body["meta"]["total"] == 2

    async def test_filter_archived(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        created = await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"type": "expense", "name": "Old"},
        )
        category_id = created.json()["id"]
        await client.patch(
            category_url(authed_user.farm_id, category_id),
            headers=authed_user.headers,
            json={"archived_at": "2026-01-01T00:00:00Z"},
        )
        await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"type": "expense", "name": "Current"},
        )

        active = await client.get(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"archived": "false"},
        )
        archived = await client.get(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"archived": "true"},
        )

        assert active.json()["meta"]["total"] == 1
        assert active.json()["data"][0]["name"] == "Current"
        assert archived.json()["meta"]["total"] == 1
        assert archived.json()["data"][0]["name"] == "Old"

    async def test_search_name(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        for name in ["Feed Grain", "Vet Visit", "Feed Hay"]:
            await client.post(
                categories_url(authed_user.farm_id),
                headers=authed_user.headers,
                json={"type": "expense", "name": name},
            )

        response = await client.get(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"q": "feed"},
        )

        assert response.json()["meta"]["total"] == 2


class TestUpdateDelete:
    async def test_update_name_and_archive(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        created = await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"type": "expense", "name": "Feed"},
        )
        category_id = created.json()["id"]

        response = await client.patch(
            category_url(authed_user.farm_id, category_id),
            headers=authed_user.headers,
            json={"name": "Feed & Grain", "archived_at": "2026-01-01T00:00:00Z"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Feed & Grain"
        assert body["archived_at"] is not None

    async def test_type_cannot_change(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        created = await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"type": "expense", "name": "Feed"},
        )
        category_id = created.json()["id"]

        response = await client.patch(
            category_url(authed_user.farm_id, category_id),
            headers=authed_user.headers,
            json={"type": "income"},
        )

        assert response.status_code == 422

    async def test_delete(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        created = await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"type": "expense", "name": "Temp"},
        )
        category_id = created.json()["id"]

        delete = await client.delete(
            category_url(authed_user.farm_id, category_id),
            headers=authed_user.headers,
        )
        assert delete.status_code == 204

        follow_up = await client.get(
            category_url(authed_user.farm_id, category_id),
            headers=authed_user.headers,
        )
        assert follow_up.status_code == 404


class TestProductOwnsItsPool:
    """A production category provisions the produce asset holding its stock, so
    "Huevos" is one thing the farmer creates rather than a category plus a
    look-alike asset that nothing kept in agreement."""

    async def test_production_category_provisions_a_produce_pool(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        response = await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"type": "production", "name": "Huevos", "unit": "unit"},
        )

        assert response.status_code == 201, response.text
        pool_id = response.json()["produce_asset_id"]
        assert pool_id is not None
        pool = await client.get(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{pool_id}",
            headers=authed_user.headers,
        )
        assert pool.status_code == 200, pool.text
        assert pool.json()["kind"] == "produce"
        assert pool.json()["name"] == "Huevos"

    async def test_non_production_category_has_no_pool(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        response = await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"type": "expense", "name": "Veterinario"},
        )

        assert response.status_code == 201, response.text
        assert response.json()["produce_asset_id"] is None

    async def test_rejected_duplicate_leaves_no_orphan_pool(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        # The category and its pool are one transaction — a name conflict must
        # not leave a stray produce asset behind.
        body = {"type": "production", "name": "Huevos", "unit": "unit"}
        first = await client.post(
            categories_url(authed_user.farm_id), headers=authed_user.headers, json=body
        )
        assert first.status_code == 201, first.text

        duplicate = await client.post(
            categories_url(authed_user.farm_id), headers=authed_user.headers, json=body
        )

        assert duplicate.status_code == 409, duplicate.text
        pools = await client.get(
            f"/api/v1/farms/{authed_user.farm_id}/assets",
            headers=authed_user.headers,
            params={"kind": "produce"},
        )
        assert pools.json()["meta"]["total"] == 1

    async def test_delete_product_retires_its_pool(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        created = await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"type": "production", "name": "Huevos", "unit": "unit"},
        )
        pool_id = created.json()["produce_asset_id"]

        delete = await client.delete(
            category_url(authed_user.farm_id, created.json()["id"]),
            headers=authed_user.headers,
        )

        assert delete.status_code == 204, delete.text
        pool = await client.get(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{pool_id}",
            headers=authed_user.headers,
        )
        assert pool.status_code == 404

    async def test_delete_product_with_recorded_stock_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets",
            headers=authed_user.headers,
            json={"name": "Gallinas", "kind": "animal", "mode": "aggregated"},
        )
        created = await client.post(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"type": "production", "name": "Huevos", "unit": "unit"},
        )
        harvested = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{flock.json()['id']}/harvests",
            headers=authed_user.headers,
            json={"quantity": "12", "unit": "unit", "category_id": created.json()["id"]},
        )
        assert harvested.status_code == 201, harvested.text

        delete = await client.delete(
            category_url(authed_user.farm_id, created.json()["id"]),
            headers=authed_user.headers,
        )

        assert delete.status_code == 422


class TestFarmScope:
    async def test_non_member_cannot_list(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("alice@example.com")
        bob = await register_user("bob@example.com")

        response = await client.get(
            categories_url(alice.farm_id),
            headers=bob.headers,
        )
        assert response.status_code == 403
