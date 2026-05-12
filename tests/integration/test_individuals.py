from collections.abc import Awaitable, Callable

from httpx import AsyncClient

from tests.conftest import AuthedUser

ANIMAL_INDIVIDUAL = {"name": "Cattle", "kind": "animal", "mode": "individual"}
ANIMAL_AGGREGATED = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}


def assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def individuals_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/individuals"


def individual_url(farm_id: int, asset_id: int, individual_id: int) -> str:
    return f"{individuals_url(farm_id, asset_id)}/{individual_id}"


async def _create_asset(client: AsyncClient, authed: AuthedUser, payload: dict[str, object]) -> int:
    resp = await client.post(assets_url(authed.farm_id), headers=authed.headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class TestCreateIndividual:
    async def test_creates_on_individual_mode_asset(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)

        response = await client.post(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"name": "Vaca A", "tag": "A-001"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Vaca A"
        assert body["tag"] == "A-001"
        assert body["status"] == "active"
        assert body["asset_id"] == asset_id

    async def test_rejects_aggregated_mode_asset(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)

        response = await client.post(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"name": "Gallina B", "tag": "G-001"},
        )

        assert response.status_code == 422
        assert "aggregated" in response.json()["detail"].lower()

    async def test_parent_from_another_farm_rejected(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("alice@example.com")
        bob = await register_user("bob@example.com")
        alice_asset = await _create_asset(client, alice, ANIMAL_INDIVIDUAL)
        bob_asset = await _create_asset(client, bob, ANIMAL_INDIVIDUAL)
        bob_parent = await client.post(
            individuals_url(bob.farm_id, bob_asset),
            headers=bob.headers,
            json={"name": "Bob's Cow", "tag": "BOB-001"},
        )
        bob_parent_id = bob_parent.json()["id"]

        response = await client.post(
            individuals_url(alice.farm_id, alice_asset),
            headers=alice.headers,
            json={"name": "Calf", "tag": "CALF-001", "mother_id": bob_parent_id},
        )

        assert response.status_code == 422
        assert "mother" in response.json()["detail"].lower()


class TestListIndividuals:
    async def test_filter_by_status(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        for name in ["A", "B", "C"]:
            await client.post(
                individuals_url(authed_user.farm_id, asset_id),
                headers=authed_user.headers,
                json={"name": name, "tag": f"TAG-{name}"},
            )
        created_c = (
            await client.get(
                individuals_url(authed_user.farm_id, asset_id),
                headers=authed_user.headers,
                params={"sort": "name"},
            )
        ).json()["data"][2]["id"]
        await client.patch(
            individual_url(authed_user.farm_id, asset_id, created_c),
            headers=authed_user.headers,
            json={"status": "sold"},
        )

        response = await client.get(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            params={"status": "active"},
        )

        body = response.json()
        assert body["meta"]["total"] == 2

    async def test_search_matches_tag(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        await client.post(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"name": "Vaca A", "tag": "TAG-001"},
        )
        await client.post(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"name": "Vaca B", "tag": "TAG-002"},
        )

        response = await client.get(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            params={"q": "001"},
        )

        body = response.json()
        assert body["meta"]["total"] == 1
        assert body["data"][0]["tag"] == "TAG-001"


class TestGetUpdateDelete:
    async def test_patch_updates_status(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        created = await client.post(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"name": "Vaca A", "tag": "VACA-A"},
        )
        individual_id = created.json()["id"]

        response = await client.patch(
            individual_url(authed_user.farm_id, asset_id, individual_id),
            headers=authed_user.headers,
            json={"status": "sold"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "sold"

    async def test_delete(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        created = await client.post(
            individuals_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"name": "Temporary", "tag": "TMP-001"},
        )
        individual_id = created.json()["id"]

        delete = await client.delete(
            individual_url(authed_user.farm_id, asset_id, individual_id),
            headers=authed_user.headers,
        )
        assert delete.status_code == 204

        follow_up = await client.get(
            individual_url(authed_user.farm_id, asset_id, individual_id),
            headers=authed_user.headers,
        )
        assert follow_up.status_code == 404

    async def test_missing_asset_returns_404(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        response = await client.get(
            individuals_url(authed_user.farm_id, 999999),
            headers=authed_user.headers,
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
        alice_asset = await _create_asset(client, alice, ANIMAL_INDIVIDUAL)

        response = await client.get(
            individuals_url(alice.farm_id, alice_asset),
            headers=bob.headers,
        )
        assert response.status_code == 403
