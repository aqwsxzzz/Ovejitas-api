"""Stage 3 — asset counts per kind (the "Activos" overview).

GET /farms/{farm_id}/assets/summary returns one {kind, count} entry per kind
present in the farm, scoped to that farm.
"""

from httpx import AsyncClient

from tests.conftest import AuthedUser


def _assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def _summary_url(farm_id: int) -> str:
    return f"{_assets_url(farm_id)}/summary"


async def _create_asset(client: AsyncClient, authed: AuthedUser, name: str, kind: str) -> None:
    resp = await client.post(
        _assets_url(authed.farm_id),
        headers=authed.headers,
        json={"name": name, "kind": kind, "mode": "aggregated"},
    )
    assert resp.status_code == 201, resp.text


class TestAssetSummary:
    async def test_returns_one_count_per_kind_present(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await _create_asset(client, authed_user, "Gallinas", "animal")
        await _create_asset(client, authed_user, "Vacas", "animal")
        await _create_asset(client, authed_user, "Maíz", "material")

        resp = await client.get(_summary_url(authed_user.farm_id), headers=authed_user.headers)

        assert resp.status_code == 200, resp.text
        counts = {row["kind"]: row["count"] for row in resp.json()["data"]}
        assert counts == {"animal": 2, "material": 1}

    async def test_empty_farm_returns_no_rows(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.get(_summary_url(authed_user.farm_id), headers=authed_user.headers)

        assert resp.status_code == 200, resp.text
        assert resp.json()["data"] == []

    async def test_counts_are_scoped_to_the_farm(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user: object,
    ) -> None:
        other = await register_user("other@example.com")  # type: ignore[operator]
        await _create_asset(client, other, "Otra granja", "animal")
        await _create_asset(client, authed_user, "Maíz", "material")

        resp = await client.get(_summary_url(authed_user.farm_id), headers=authed_user.headers)

        assert resp.status_code == 200, resp.text
        counts = {row["kind"]: row["count"] for row in resp.json()["data"]}
        assert counts == {"material": 1}

    async def test_non_member_is_forbidden(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.get(
            _summary_url(authed_user.farm_id + 999), headers=authed_user.headers
        )

        assert resp.status_code == 403
