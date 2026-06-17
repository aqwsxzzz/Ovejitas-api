"""Stage 2 verification — the unfiltered event listing must return inventory
events alongside expense/income.

A material purchase emits TWO events on the material asset: an inventory
increment and an expense. Listing that asset's events with no ``type`` filter
must return both, and pagination totals must count the inventory row.
"""

from httpx import AsyncClient

from tests.conftest import AuthedUser

MATERIAL = {"name": "Maíz", "kind": "material", "mode": "aggregated"}


def _assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def _events_url(farm_id: int, asset_id: int) -> str:
    return f"{_assets_url(farm_id)}/{asset_id}/events"


def _purchases_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/material-purchases"


async def _create_material(client: AsyncClient, authed: AuthedUser) -> int:
    resp = await client.post(_assets_url(authed.farm_id), headers=authed.headers, json=MATERIAL)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _purchase(client: AsyncClient, authed: AuthedUser, material_id: int) -> None:
    resp = await client.post(
        _purchases_url(authed.farm_id),
        headers=authed.headers,
        json={
            "material_asset_id": material_id,
            "occurred_at": "2026-04-20T10:00:00Z",
            "quantity": "50",
            "unit": "kg",
            "amount": "40",
        },
    )
    assert resp.status_code == 201, resp.text


class TestUnfilteredListingIncludesInventory:
    async def test_no_type_filter_returns_inventory_and_expense(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_material(client, authed_user)
        await _purchase(client, authed_user, material_id)

        resp = await client.get(
            _events_url(authed_user.farm_id, material_id), headers=authed_user.headers
        )

        assert resp.status_code == 200, resp.text
        types = {row["type"] for row in resp.json()["data"]}
        assert {"inventory", "expense"} <= types

    async def test_total_counts_the_inventory_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        material_id = await _create_material(client, authed_user)
        await _purchase(client, authed_user, material_id)

        resp = await client.get(
            _events_url(authed_user.farm_id, material_id), headers=authed_user.headers
        )

        assert resp.status_code == 200, resp.text
        # the purchase emitted exactly two events; both must be counted
        assert resp.json()["meta"]["total"] == 2
