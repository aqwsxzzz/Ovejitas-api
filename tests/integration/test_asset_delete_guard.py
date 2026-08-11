"""Deleting an asset the farm still has records for is refused, not crashed.

Six RESTRICT foreign keys point at ``asset.id``. Before this guard the refusal
escaped as an unhandled IntegrityError, so the client got a 500 with an empty
body and could not tell "this flock has harvests" from "the backend is down".
"""

from collections.abc import Awaitable, Callable

from httpx import AsyncClient

from tests.conftest import AuthedUser

FLOCK = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}
MATERIAL = {"name": "Maiz", "kind": "material", "mode": "aggregated"}


def assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def asset_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}"


async def _create_asset(client: AsyncClient, authed: AuthedUser, payload: dict[str, str]) -> int:
    resp = await client.post(assets_url(authed.farm_id), headers=authed.headers, json=payload)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _harvested_flock(client: AsyncClient, authed: AuthedUser) -> tuple[int, int]:
    """A flock that has harvested into a product's pool. Returns (flock, pool)."""
    flock_id = await _create_asset(client, authed, FLOCK)
    product = await client.post(
        f"/api/v1/farms/{authed.farm_id}/event-categories",
        headers=authed.headers,
        json={"type": "production", "name": "Huevos", "unit": "unit"},
    )
    assert product.status_code == 201, product.text
    harvest = await client.post(
        f"{asset_url(authed.farm_id, flock_id)}/harvests",
        headers=authed.headers,
        json={"quantity": "15", "unit": "unit", "category_id": product.json()["id"]},
    )
    assert harvest.status_code == 201, harvest.text
    return flock_id, int(product.json()["produce_asset_id"])


async def _fed_flock(client: AsyncClient, authed: AuthedUser) -> tuple[int, int]:
    """A flock that has eaten a purchased material. Returns (flock, material)."""
    flock_id = await _create_asset(client, authed, FLOCK)
    material_id = await _create_asset(client, authed, MATERIAL)
    purchase = await client.post(
        f"/api/v1/farms/{authed.farm_id}/material-purchases",
        headers=authed.headers,
        json={
            "material_asset_id": material_id,
            "occurred_at": "2026-04-20T10:00:00Z",
            "quantity": "50",
            "unit": "kg",
            "amount": "40",
        },
    )
    assert purchase.status_code == 201, purchase.text
    consumption = await client.post(
        f"/api/v1/farms/{authed.farm_id}/material-consumptions",
        headers=authed.headers,
        json={
            "material_asset_id": material_id,
            "consumer_asset_id": flock_id,
            "occurred_at": "2026-04-21T10:00:00Z",
            "quantity": "30",
            "unit": "kg",
            "reason": "feeding",
        },
    )
    assert consumption.status_code == 201, consumption.text
    return flock_id, material_id


class TestBlockedDelete:
    async def test_delete_producer_with_harvests_returns_409(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock_id, _ = await _harvested_flock(client, authed_user)

        response = await client.delete(
            asset_url(authed_user.farm_id, flock_id), headers=authed_user.headers
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Cannot delete an asset with recorded harvests"

    async def test_delete_produce_pool_returns_409(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        _, pool_id = await _harvested_flock(client, authed_user)

        response = await client.delete(
            asset_url(authed_user.farm_id, pool_id), headers=authed_user.headers
        )

        assert response.status_code == 409
        assert "produce pool" in response.json()["detail"]

    async def test_delete_consumer_with_feed_consumption_returns_409(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock_id, _ = await _fed_flock(client, authed_user)

        response = await client.delete(
            asset_url(authed_user.farm_id, flock_id), headers=authed_user.headers
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Cannot delete an asset with recorded feed consumption"

    async def test_delete_consumed_material_returns_409(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        _, material_id = await _fed_flock(client, authed_user)

        response = await client.delete(
            asset_url(authed_user.farm_id, material_id), headers=authed_user.headers
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Cannot delete a material with recorded consumption"

    async def test_delete_purchased_material_returns_409(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_asset(client, authed_user, MATERIAL)
        purchase = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/material-purchases",
            headers=authed_user.headers,
            json={
                "material_asset_id": material_id,
                "occurred_at": "2026-04-20T10:00:00Z",
                "quantity": "50",
                "unit": "kg",
                "amount": "40",
            },
        )
        assert purchase.status_code == 201, purchase.text

        response = await client.delete(
            asset_url(authed_user.farm_id, material_id), headers=authed_user.headers
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Cannot delete a material with recorded purchases"

    async def test_session_stays_usable_after_a_blocked_delete(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock_id, _ = await _harvested_flock(client, authed_user)
        blocked = await client.delete(
            asset_url(authed_user.farm_id, flock_id), headers=authed_user.headers
        )
        assert blocked.status_code == 409

        response = await client.post(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"name": "Tractor", "kind": "equipment"},
        )

        assert response.status_code == 201, response.text

    async def test_delete_clean_asset_still_returns_204(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, FLOCK)

        response = await client.delete(
            asset_url(authed_user.farm_id, asset_id), headers=authed_user.headers
        )

        assert response.status_code == 204

    async def test_non_member_cannot_delete(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("alice@example.com")
        bob = await register_user("bob@example.com")
        asset_id = await _create_asset(client, alice, FLOCK)

        response = await client.delete(asset_url(alice.farm_id, asset_id), headers=bob.headers)

        assert response.status_code == 403
