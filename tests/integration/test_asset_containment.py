"""Containment: an asset points at the location asset holding it.

The point of the link over the free text it replaced is that it survives a
rename, so that is the first thing asserted here.
"""

from collections.abc import Awaitable, Callable

from httpx import AsyncClient

from tests.conftest import AuthedUser

FLOCK = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}


def assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def asset_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}"


async def _create_asset(client: AsyncClient, authed: AuthedUser, payload: dict[str, object]) -> int:
    resp = await client.post(assets_url(authed.farm_id), headers=authed.headers, json=payload)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _location(client: AsyncClient, authed: AuthedUser, name: str = "Potrero sur") -> int:
    return await _create_asset(client, authed, {"name": name, "kind": "location"})


class TestContainment:
    async def test_asset_is_created_inside_a_location(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        potrero_id = await _location(client, authed_user)

        response = await client.post(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={**FLOCK, "location_asset_id": potrero_id},
        )

        assert response.status_code == 201, response.text
        assert response.json()["location_asset_id"] == potrero_id

    async def test_link_survives_renaming_the_location(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        potrero_id = await _location(client, authed_user)
        flock_id = await _create_asset(
            client, authed_user, {**FLOCK, "location_asset_id": potrero_id}
        )

        rename = await client.patch(
            asset_url(authed_user.farm_id, potrero_id),
            headers=authed_user.headers,
            json={"name": "Potrero norte"},
        )

        assert rename.status_code == 200, rename.text
        flock = await client.get(
            asset_url(authed_user.farm_id, flock_id), headers=authed_user.headers
        )
        assert flock.json()["location_asset_id"] == potrero_id

    async def test_assets_are_listable_by_location(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        potrero_id = await _location(client, authed_user)
        inside_id = await _create_asset(
            client, authed_user, {**FLOCK, "location_asset_id": potrero_id}
        )
        await _create_asset(client, authed_user, FLOCK)

        listing = await client.get(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"location_asset_id": potrero_id},
        )

        assert listing.status_code == 200
        assert [row["id"] for row in listing.json()["data"]] == [inside_id]

    async def test_locations_nest(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        field_id = await _location(client, authed_user, "Campo")
        paddock_id = await _location(client, authed_user, "Potrero")

        response = await client.patch(
            asset_url(authed_user.farm_id, paddock_id),
            headers=authed_user.headers,
            json={"location_asset_id": field_id},
        )

        assert response.status_code == 200, response.text
        assert response.json()["location_asset_id"] == field_id

    async def test_moving_out_of_a_location_clears_the_link(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        potrero_id = await _location(client, authed_user)
        flock_id = await _create_asset(
            client, authed_user, {**FLOCK, "location_asset_id": potrero_id}
        )

        response = await client.patch(
            asset_url(authed_user.farm_id, flock_id),
            headers=authed_user.headers,
            json={"location_asset_id": None},
        )

        assert response.status_code == 200, response.text
        assert response.json()["location_asset_id"] is None

    async def test_deleting_a_location_clears_the_link(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        potrero_id = await _location(client, authed_user)
        flock_id = await _create_asset(
            client, authed_user, {**FLOCK, "location_asset_id": potrero_id}
        )

        deleted = await client.delete(
            asset_url(authed_user.farm_id, potrero_id), headers=authed_user.headers
        )

        assert deleted.status_code == 204, deleted.text
        flock = await client.get(
            asset_url(authed_user.farm_id, flock_id), headers=authed_user.headers
        )
        assert flock.status_code == 200
        assert flock.json()["location_asset_id"] is None


class TestContainmentRejections:
    async def test_non_location_target_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        other_flock_id = await _create_asset(client, authed_user, FLOCK)

        response = await client.post(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={**FLOCK, "location_asset_id": other_flock_id},
        )

        assert response.status_code == 422
        assert "location asset" in response.json()["detail"]

    async def test_asset_cannot_be_its_own_location(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        potrero_id = await _location(client, authed_user)

        response = await client.patch(
            asset_url(authed_user.farm_id, potrero_id),
            headers=authed_user.headers,
            json={"location_asset_id": potrero_id},
        )

        assert response.status_code == 422
        assert "contained by itself" in response.json()["detail"]

    async def test_cycle_through_a_chain_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        field_id = await _location(client, authed_user, "Campo")
        paddock_id = await _location(client, authed_user, "Potrero")
        await client.patch(
            asset_url(authed_user.farm_id, paddock_id),
            headers=authed_user.headers,
            json={"location_asset_id": field_id},
        )

        response = await client.patch(
            asset_url(authed_user.farm_id, field_id),
            headers=authed_user.headers,
            json={"location_asset_id": paddock_id},
        )

        assert response.status_code == 422
        assert "contained by itself" in response.json()["detail"]

    async def test_location_from_another_farm_rejected(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("alice@example.com")
        bob = await register_user("bob@example.com")
        alice_location = await _location(client, alice)

        response = await client.post(
            assets_url(bob.farm_id),
            headers=bob.headers,
            json={**FLOCK, "location_asset_id": alice_location},
        )

        assert response.status_code == 404
