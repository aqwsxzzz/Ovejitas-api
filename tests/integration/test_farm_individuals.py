"""The farm-wide individual list.

Rams and bulls are commonly kept in their own lot, so the sire a farmer needs to
name on a pregnancy check is exactly the individual the per-asset list cannot
reach. These cover that the farm boundary still holds.
"""

from collections.abc import Awaitable, Callable

from httpx import AsyncClient

from tests.conftest import AuthedUser

HERD = {"name": "Vacas", "kind": "animal", "mode": "individual"}
SIRES = {"name": "Toros", "kind": "animal", "mode": "individual"}


def assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def farm_individuals_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/individuals"


async def _create_asset(client: AsyncClient, authed: AuthedUser, payload: dict[str, str]) -> int:
    resp = await client.post(assets_url(authed.farm_id), headers=authed.headers, json=payload)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _create_individual(
    client: AsyncClient, authed: AuthedUser, asset_id: int, tag: str, name: str | None = None
) -> int:
    resp = await client.post(
        f"{assets_url(authed.farm_id)}/{asset_id}/individuals",
        headers=authed.headers,
        json={"tag": tag, "name": name},
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _two_lots(client: AsyncClient, authed: AuthedUser) -> tuple[int, int]:
    """A cow in the herd and a bull kept apart. Returns (cow_id, bull_id)."""
    herd_id = await _create_asset(client, authed, HERD)
    sires_id = await _create_asset(client, authed, SIRES)
    cow_id = await _create_individual(client, authed, herd_id, "V-001", "Aurora")
    bull_id = await _create_individual(client, authed, sires_id, "T-001", "Bruno")
    return cow_id, bull_id


async def _listed(
    client: AsyncClient, authed: AuthedUser, **params: str
) -> list[dict[str, object]]:
    resp = await client.get(
        farm_individuals_url(authed.farm_id), headers=authed.headers, params=params
    )
    assert resp.status_code == 200, resp.text
    rows: list[dict[str, object]] = resp.json()["data"]
    return rows


class TestFarmIndividualList:
    async def test_returns_individuals_from_every_lot(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        cow_id, bull_id = await _two_lots(client, authed_user)

        ids = [row["id"] for row in await _listed(client, authed_user)]

        assert cow_id in ids
        assert bull_id in ids

    async def test_filters_by_status(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        herd_id = await _create_asset(client, authed_user, HERD)
        active_id = await _create_individual(client, authed_user, herd_id, "V-001")
        sold_id = await _create_individual(client, authed_user, herd_id, "V-002")
        sale = await client.patch(
            f"{assets_url(authed_user.farm_id)}/{herd_id}/individuals/{sold_id}",
            headers=authed_user.headers,
            json={"status": "sold", "sale_amount": "500"},
        )
        assert sale.status_code == 200, sale.text

        ids = [row["id"] for row in await _listed(client, authed_user, status="active")]

        assert ids == [active_id]

    async def test_filters_by_asset(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        herd_id = await _create_asset(client, authed_user, HERD)
        sires_id = await _create_asset(client, authed_user, SIRES)
        await _create_individual(client, authed_user, herd_id, "V-001")
        bull_id = await _create_individual(client, authed_user, sires_id, "T-001")

        ids = [row["id"] for row in await _listed(client, authed_user, asset_id=str(sires_id))]

        assert ids == [bull_id]

    async def test_searches_by_tag(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        _, bull_id = await _two_lots(client, authed_user)

        ids = [row["id"] for row in await _listed(client, authed_user, q="T-00")]

        assert ids == [bull_id]

    async def test_searches_by_name(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        _, bull_id = await _two_lots(client, authed_user)

        ids = [row["id"] for row in await _listed(client, authed_user, q="bruno")]

        assert ids == [bull_id]

    async def test_paginates_with_a_stable_total(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        herd_id = await _create_asset(client, authed_user, HERD)
        for i in range(3):
            await _create_individual(client, authed_user, herd_id, f"V-{i:03d}")

        resp = await client.get(
            farm_individuals_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"page": 2, "page_size": 2},
        )

        assert resp.status_code == 200
        meta = resp.json()["meta"]
        assert meta["total"] == 3
        assert meta["has_next"] is False
        assert len(resp.json()["data"]) == 1


class TestFarmScope:
    async def test_excludes_individuals_from_another_farm(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("alice@example.com")
        bob = await register_user("bob@example.com")
        alice_asset = await _create_asset(client, alice, HERD)
        await _create_individual(client, alice, alice_asset, "A-001")
        bob_asset = await _create_asset(client, bob, HERD)
        bob_individual = await _create_individual(client, bob, bob_asset, "B-001")

        ids = [row["id"] for row in await _listed(client, bob)]

        assert ids == [bob_individual]

    async def test_asset_id_from_another_farm_matches_nothing(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("alice@example.com")
        bob = await register_user("bob@example.com")
        alice_asset = await _create_asset(client, alice, HERD)
        await _create_individual(client, alice, alice_asset, "A-001")

        rows = await _listed(client, bob, asset_id=str(alice_asset))

        assert rows == []

    async def test_non_member_cannot_list(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("alice@example.com")
        bob = await register_user("bob@example.com")

        response = await client.get(farm_individuals_url(alice.farm_id), headers=bob.headers)

        assert response.status_code == 403
