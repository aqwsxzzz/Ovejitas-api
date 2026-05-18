from collections.abc import Awaitable, Callable

from httpx import AsyncClient

from tests.conftest import AuthedUser


def assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def asset_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}"


AGGREGATED_ANIMAL = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}


async def _create(client: AsyncClient, authed: AuthedUser, body: dict[str, str]) -> int:
    resp = await client.post(assets_url(authed.farm_id), headers=authed.headers, json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class TestCreateAsset:
    async def test_creates_and_returns_asset(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        response = await client.post(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=AGGREGATED_ANIMAL,
        )

        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Gallinas"
        assert body["kind"] == "animal"
        assert body["mode"] == "aggregated"
        assert body["farm_id"] == authed_user.farm_id

    async def test_invalid_kind_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        response = await client.post(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"name": "X", "kind": "dragon", "mode": "aggregated"},
        )
        assert response.status_code == 422


class TestListAssets:
    async def test_returns_paginated_envelope(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        for i in range(25):
            await client.post(
                assets_url(authed_user.farm_id),
                headers=authed_user.headers,
                json={**AGGREGATED_ANIMAL, "name": f"Batch-{i:02d}"},
            )

        response = await client.get(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"page": 1, "page_size": 10},
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 10
        assert body["meta"]["total"] == 25
        assert body["meta"]["has_next"] is True

    async def test_filter_by_kind(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        await client.post(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=AGGREGATED_ANIMAL,
        )
        await client.post(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"name": "Maíz norte", "kind": "crop", "mode": "aggregated"},
        )

        response = await client.get(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"kind": "crop"},
        )

        body = response.json()
        assert body["meta"]["total"] == 1
        assert body["data"][0]["kind"] == "crop"

    async def test_search_matches_name(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        await client.post(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=AGGREGATED_ANIMAL,
        )
        await client.post(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"name": "Vacas lecheras", "kind": "animal", "mode": "individual"},
        )

        response = await client.get(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"q": "vaca"},
        )

        body = response.json()
        assert body["meta"]["total"] == 1
        assert body["data"][0]["name"] == "Vacas lecheras"

    async def test_sort_by_name_asc(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        for name in ["Charlie", "Alpha", "Bravo"]:
            await client.post(
                assets_url(authed_user.farm_id),
                headers=authed_user.headers,
                json={**AGGREGATED_ANIMAL, "name": name},
            )

        response = await client.get(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"sort": "name"},
        )

        names = [asset["name"] for asset in response.json()["data"]]
        assert names == ["Alpha", "Bravo", "Charlie"]

    async def test_invalid_sort_field_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        response = await client.get(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"sort": "password_hash"},
        )
        assert response.status_code == 422


class TestGetUpdateDelete:
    async def test_get_returns_single_asset(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        created = await client.post(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=AGGREGATED_ANIMAL,
        )
        asset_id = created.json()["id"]

        response = await client.get(
            asset_url(authed_user.farm_id, asset_id), headers=authed_user.headers
        )

        assert response.status_code == 200
        assert response.json()["id"] == asset_id

    async def test_patch_updates_only_provided_fields(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        created = await client.post(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=AGGREGATED_ANIMAL,
        )
        asset_id = created.json()["id"]

        response = await client.patch(
            asset_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"location": "Galpón norte"},
        )

        body = response.json()
        assert body["location"] == "Galpón norte"
        assert body["name"] == "Gallinas"

    async def test_delete_removes_asset(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        created = await client.post(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=AGGREGATED_ANIMAL,
        )
        asset_id = created.json()["id"]

        delete = await client.delete(
            asset_url(authed_user.farm_id, asset_id), headers=authed_user.headers
        )
        assert delete.status_code == 204

        follow_up = await client.get(
            asset_url(authed_user.farm_id, asset_id), headers=authed_user.headers
        )
        assert follow_up.status_code == 404

    async def test_missing_asset_returns_404(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        response = await client.get(
            asset_url(authed_user.farm_id, 999999), headers=authed_user.headers
        )
        assert response.status_code == 404


class TestFarmScope:
    async def test_non_member_cannot_list(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("alice@example.com")
        bob = await register_user("bob@example.com")

        response = await client.get(assets_url(alice.farm_id), headers=bob.headers)
        assert response.status_code == 403

    async def test_non_member_cannot_create(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("alice@example.com")
        bob = await register_user("bob@example.com")

        response = await client.post(
            assets_url(alice.farm_id),
            headers=bob.headers,
            json=AGGREGATED_ANIMAL,
        )
        assert response.status_code == 403

    async def test_unauthenticated_request_returns_401(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        response = await client.get(assets_url(authed_user.farm_id))
        assert response.status_code == 401


class TestStructuralImmutability:
    """kind/mode are structural — once an asset has events, changing them would
    orphan that history, so the change is rejected."""

    async def test_kind_change_blocked_once_events_exist(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create(client, authed_user, AGGREGATED_ANIMAL)
        event = await client.post(
            f"{asset_url(authed_user.farm_id, asset_id)}/events",
            headers=authed_user.headers,
            json={"type": "observation", "occurred_at": "2026-04-20T10:00:00Z"},
        )
        assert event.status_code == 201, event.text

        patched = await client.patch(
            asset_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"kind": "crop"},
        )
        assert patched.status_code == 422

    async def test_kind_change_allowed_with_no_events(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create(client, authed_user, AGGREGATED_ANIMAL)

        patched = await client.patch(
            asset_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"kind": "crop"},
        )
        assert patched.status_code == 200
        assert patched.json()["kind"] == "crop"
