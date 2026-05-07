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
