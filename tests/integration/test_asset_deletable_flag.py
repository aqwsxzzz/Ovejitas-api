"""``AssetRead.deletable`` tells the client the delete outcome before it tries.

The flag and the guard read the same declarations, so the two cannot disagree —
these tests assert that agreement in both directions rather than the flag alone.
"""

from httpx import AsyncClient

from tests.conftest import AuthedUser
from tests.integration.test_asset_delete_guard import (
    FLOCK,
    _create_asset,
    _harvested_flock,
    asset_url,
    assets_url,
)


class TestDeletableFlag:
    async def test_fresh_asset_is_deletable(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        response = await client.post(
            assets_url(authed_user.farm_id), headers=authed_user.headers, json=FLOCK
        )

        assert response.status_code == 201, response.text
        assert response.json()["deletable"] is True

    async def test_producer_with_harvests_is_not_deletable(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock_id, _ = await _harvested_flock(client, authed_user)

        response = await client.get(
            asset_url(authed_user.farm_id, flock_id), headers=authed_user.headers
        )

        assert response.status_code == 200
        assert response.json()["deletable"] is False

    async def test_list_reports_the_flag_per_row(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock_id, pool_id = await _harvested_flock(client, authed_user)
        clean_id = await _create_asset(client, authed_user, FLOCK)

        response = await client.get(assets_url(authed_user.farm_id), headers=authed_user.headers)

        assert response.status_code == 200
        flags = {row["id"]: row["deletable"] for row in response.json()["data"]}
        assert flags[flock_id] is False
        assert flags[pool_id] is False
        assert flags[clean_id] is True

    async def test_flag_agrees_with_the_delete_outcome(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock_id, _ = await _harvested_flock(client, authed_user)
        clean_id = await _create_asset(client, authed_user, FLOCK)

        listing = await client.get(assets_url(authed_user.farm_id), headers=authed_user.headers)
        flags = {row["id"]: row["deletable"] for row in listing.json()["data"]}
        outcomes = {
            asset_id: (
                await client.delete(
                    asset_url(authed_user.farm_id, asset_id), headers=authed_user.headers
                )
            ).status_code
            for asset_id in (flock_id, clean_id)
        }

        assert outcomes[flock_id] == 409 and flags[flock_id] is False
        assert outcomes[clean_id] == 204 and flags[clean_id] is True
