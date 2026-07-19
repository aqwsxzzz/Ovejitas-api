"""Sales value report — realized average price per unit sold, per asset."""

from httpx import AsyncClient

from ovejitas.features.asset.models import AssetKind, AssetMode
from tests.conftest import AuthedUser
from tests.factories import AssetFactory

OCCURRED = "2026-06-05T10:00:00Z"


def _url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/reports/sales-value"


async def _eggs_asset(farm_id: int) -> int:
    asset = await AssetFactory.create_async(
        farm_id=farm_id, name="Eggs", kind=AssetKind.MATERIAL, mode=AssetMode.AGGREGATED
    )
    return int(asset.id)


async def _increment(
    client: AsyncClient, authed: AuthedUser, asset_id: int, quantity: str, unit: str = "unit"
) -> None:
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/assets/{asset_id}/events",
        headers=authed.headers,
        json={
            "type": "inventory",
            "occurred_at": "2026-06-01T10:00:00Z",
            "adjustment": "increment",
            "quantity": quantity,
            "unit": unit,
        },
    )
    assert resp.status_code == 201, resp.text


async def _sell(
    client: AsyncClient,
    authed: AuthedUser,
    asset_id: int,
    quantity: str,
    amount: str,
    unit: str = "unit",
) -> None:
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/assets/{asset_id}/sales",
        headers=authed.headers,
        json={"occurred_at": OCCURRED, "quantity": quantity, "unit": unit, "amount": amount},
    )
    assert resp.status_code == 201, resp.text


async def _rows(client: AsyncClient, authed: AuthedUser) -> list[dict]:
    resp = await client.get(_url(authed.farm_id), headers=authed.headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


class TestSalesValue:
    async def test_value_per_unit_from_a_sale(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        eggs = await _eggs_asset(authed_user.farm_id)
        await _increment(client, authed_user, eggs, "100")
        await _sell(client, authed_user, eggs, "24", "240")

        rows = await _rows(client, authed_user)
        assert len(rows) == 1
        row = rows[0]
        assert row["asset_id"] == eggs
        assert row["income_total"] == "240.00"
        assert row["unit"] == "unit"
        assert row["quantity_sold"] == "24"
        assert row["value_per_unit"] == "10.0000"
        assert row["ambiguous"] is False

    async def test_weighted_average_across_sales(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        eggs = await _eggs_asset(authed_user.farm_id)
        await _increment(client, authed_user, eggs, "100")
        await _sell(client, authed_user, eggs, "10", "100")
        await _sell(client, authed_user, eggs, "10", "120")

        row = (await _rows(client, authed_user))[0]
        assert row["quantity_sold"] == "20"
        assert row["income_total"] == "220.00"
        assert row["value_per_unit"] == "11.0000"  # 220 / 20

    async def test_mixed_units_marks_ambiguous(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        eggs = await _eggs_asset(authed_user.farm_id)
        await _increment(client, authed_user, eggs, "100", unit="unit")
        await _increment(client, authed_user, eggs, "20", unit="dozen")
        await _sell(client, authed_user, eggs, "12", "120", unit="unit")
        await _sell(client, authed_user, eggs, "1", "18", unit="dozen")

        row = (await _rows(client, authed_user))[0]
        assert row["income_total"] == "138.00"
        assert row["unit"] is None
        assert row["quantity_sold"] is None
        assert row["value_per_unit"] is None
        assert row["ambiguous"] is True

    async def test_manual_income_is_excluded(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        eggs = await _eggs_asset(authed_user.farm_id)
        await _increment(client, authed_user, eggs, "100")
        await _sell(client, authed_user, eggs, "24", "240")
        # a hand-entered INCOME (no payload.source) must not skew the average
        manual = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{eggs}/events",
            headers=authed_user.headers,
            json={"type": "income", "occurred_at": OCCURRED, "amount": "1000"},
        )
        assert manual.status_code == 201, manual.text

        row = (await _rows(client, authed_user))[0]
        assert row["income_total"] == "240.00"
        assert row["value_per_unit"] == "10.0000"

    async def test_asset_without_sales_is_absent(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        eggs = await _eggs_asset(authed_user.farm_id)
        await _increment(client, authed_user, eggs, "100")  # stock but never sold

        assert await _rows(client, authed_user) == []
