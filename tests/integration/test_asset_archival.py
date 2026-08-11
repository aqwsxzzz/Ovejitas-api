"""Retiring an asset without destroying what it produced.

An asset with events cannot change kind or mode, and cannot be deleted once it
carries harvests. Archival is the third option that keeps a sold flock out of
every picker while leaving its history exactly where the reports expect it.
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

ARCHIVED_AT = "2026-08-01T10:00:00Z"


async def _archive(client: AsyncClient, authed: AuthedUser, asset_id: int) -> dict[str, object]:
    resp = await client.patch(
        asset_url(authed.farm_id, asset_id),
        headers=authed.headers,
        json={"archived_at": ARCHIVED_AT},
    )
    assert resp.status_code == 200, resp.text
    body: dict[str, object] = resp.json()
    return body


async def _list_ids(client: AsyncClient, authed: AuthedUser, **params: str) -> list[int]:
    resp = await client.get(assets_url(authed.farm_id), headers=authed.headers, params=params)
    assert resp.status_code == 200, resp.text
    return [row["id"] for row in resp.json()["data"]]


class TestArchive:
    async def test_archive_and_unarchive_round_trip(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, FLOCK)

        archived = await _archive(client, authed_user, asset_id)
        unarchived = await client.patch(
            asset_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={"archived_at": None},
        )

        assert archived["archived_at"] is not None
        assert unarchived.status_code == 200, unarchived.text
        assert unarchived.json()["archived_at"] is None

    async def test_archiving_an_asset_with_harvests_succeeds(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock_id, _ = await _harvested_flock(client, authed_user)

        archived = await _archive(client, authed_user, flock_id)

        assert archived["archived_at"] is not None

    async def test_archiving_leaves_the_harvest_readable(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock_id, pool_id = await _harvested_flock(client, authed_user)

        await _archive(client, authed_user, flock_id)

        balance = await client.get(
            f"{asset_url(authed_user.farm_id, pool_id)}/events/balance",
            headers=authed_user.headers,
        )
        assert balance.status_code == 200
        assert balance.json()["balances"][0]["on_hand"] == "15"

    async def test_archived_asset_absent_from_default_list(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        retired_id = await _create_asset(client, authed_user, FLOCK)
        active_id = await _create_asset(client, authed_user, FLOCK)
        await _archive(client, authed_user, retired_id)

        ids = await _list_ids(client, authed_user)

        assert retired_id not in ids
        assert active_id in ids

    async def test_archived_filter_returns_only_archived(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        retired_id = await _create_asset(client, authed_user, FLOCK)
        active_id = await _create_asset(client, authed_user, FLOCK)
        await _archive(client, authed_user, retired_id)

        ids = await _list_ids(client, authed_user, archived="true")

        assert ids == [retired_id]
        assert active_id not in ids

    async def test_archived_asset_still_fetchable_by_id(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, FLOCK)
        await _archive(client, authed_user, asset_id)

        response = await client.get(
            asset_url(authed_user.farm_id, asset_id), headers=authed_user.headers
        )

        assert response.status_code == 200
        assert response.json()["archived_at"] is not None

    async def test_archived_asset_excluded_from_kind_summary(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        retired_id = await _create_asset(client, authed_user, FLOCK)
        await _create_asset(client, authed_user, FLOCK)
        await _archive(client, authed_user, retired_id)

        response = await client.get(
            f"{assets_url(authed_user.farm_id)}/summary", headers=authed_user.headers
        )

        assert response.status_code == 200
        counts = {row["kind"]: row["count"] for row in response.json()["data"]}
        assert counts["animal"] == 1
