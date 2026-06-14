"""Coop productivity report — eggs laid vs expected (per-head model).

Headcount is the live HEAD on-hand derived from flock acquisitions, not a
stored field, so tests build it by recording a flock acquisition.
"""

from datetime import UTC, datetime
from decimal import Decimal

from httpx import AsyncClient

from ovejitas.features.event.types import EventType
from tests.conftest import AuthedUser
from tests.factories import AssetFactory, EventFactory

# A full 10-day window: 2026-06-01 .. 2026-06-10 inclusive (midnight date_to is
# rolled to the next midnight by the shared whole-day rule).
JUNE = {"date_from": "2026-06-01T00:00:00Z", "date_to": "2026-06-10T00:00:00Z"}


def _url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/reports/coop-productivity"


async def _coop(farm_id: int, **kw: object) -> int:
    asset = await AssetFactory.create_async(farm_id=farm_id, **kw)
    return int(asset.id)


async def _stock_flock(
    client: AsyncClient, authed: AuthedUser, asset_id: int, quantity: int
) -> None:
    """Set the coop's headcount by recording a flock acquisition."""
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/assets/{asset_id}/flock/acquisitions",
        headers=authed.headers,
        json={"quantity": quantity},
    )
    assert resp.status_code == 201, resp.text


async def _lay(farm_id: int, asset_id: int, user_id: int, quantity: str, unit: str) -> None:
    await EventFactory.create_async(
        farm_id=farm_id,
        asset_id=asset_id,
        created_by=user_id,
        type=EventType.PRODUCTION,
        quantity=Decimal(quantity),
        unit=unit,
        occurred_at=datetime(2026, 6, 5, 9, 0, tzinfo=UTC),
    )


class TestCoopProductivity:
    async def test_configured_coop_reports_percentage(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        coop = await _coop(
            authed_user.farm_id, name="Gallinas", expected_eggs_per_head_per_day=Decimal("0.8")
        )
        await _stock_flock(client, authed_user, coop, 10)
        await _lay(authed_user.farm_id, coop, authed_user.user_id, "64", "unit")

        resp = await client.get(_url(authed_user.farm_id), headers=authed_user.headers, params=JUNE)

        assert resp.status_code == 200, resp.text
        row = resp.json()["data"][0]
        assert row["asset_id"] == coop
        assert Decimal(row["produced"]) == Decimal("64")
        assert Decimal(row["expected"]) == Decimal("80")  # 0.8 x 10 head x 10 days
        assert Decimal(row["productivity_pct"]) == Decimal("80.0")
        assert row["missing_capacity"] is False

    async def test_coop_without_rate_flags_missing_capacity(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        coop = await _coop(authed_user.farm_id, name="Gallinas")  # no rate
        await _stock_flock(client, authed_user, coop, 10)
        await _lay(authed_user.farm_id, coop, authed_user.user_id, "30", "unit")

        resp = await client.get(_url(authed_user.farm_id), headers=authed_user.headers, params=JUNE)

        row = resp.json()["data"][0]
        assert Decimal(row["produced"]) == Decimal("30")
        assert row["expected"] is None
        assert row["productivity_pct"] is None
        assert row["missing_capacity"] is True

    async def test_rate_set_but_no_flock_flags_missing_capacity(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        # Rate configured, but no acquisition recorded → headcount is 0, so there
        # is no denominator yet.
        coop = await _coop(
            authed_user.farm_id, name="Gallinas", expected_eggs_per_head_per_day=Decimal("0.8")
        )
        await _lay(authed_user.farm_id, coop, authed_user.user_id, "20", "unit")

        resp = await client.get(_url(authed_user.farm_id), headers=authed_user.headers, params=JUNE)

        row = resp.json()["data"][0]
        assert Decimal(row["produced"]) == Decimal("20")
        assert row["expected"] is None
        assert row["missing_capacity"] is True

    async def test_dozen_production_normalized_to_eggs(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        coop = await _coop(
            authed_user.farm_id, name="Gallinas", expected_eggs_per_head_per_day=Decimal("0.8")
        )
        await _stock_flock(client, authed_user, coop, 10)
        await _lay(authed_user.farm_id, coop, authed_user.user_id, "5", "dozen")  # 60 eggs

        resp = await client.get(_url(authed_user.farm_id), headers=authed_user.headers, params=JUNE)

        row = resp.json()["data"][0]
        assert Decimal(row["produced"]) == Decimal("60")
        assert Decimal(row["productivity_pct"]) == Decimal("75.0")  # 60 / 80

    async def test_configured_coop_with_no_production_reports_zero(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        coop = await _coop(
            authed_user.farm_id, name="Gallinas", expected_eggs_per_head_per_day=Decimal("0.8")
        )
        await _stock_flock(client, authed_user, coop, 10)

        resp = await client.get(_url(authed_user.farm_id), headers=authed_user.headers, params=JUNE)

        row = resp.json()["data"][0]
        assert row["asset_id"] == coop
        assert Decimal(row["produced"]) == Decimal("0")
        assert Decimal(row["productivity_pct"]) == Decimal("0.0")
        assert row["missing_capacity"] is False

    async def test_missing_period_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.get(_url(authed_user.farm_id), headers=authed_user.headers)
        assert resp.status_code == 422
