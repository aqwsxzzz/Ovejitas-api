"""Production-productivity report — produced vs expected per (asset, product).

Headcount is time-weighted (animal-days), so HEAD inventory is inserted with an
explicit occurred_at before the window; production events carry a category_id.
"""

from datetime import UTC, datetime
from decimal import Decimal

from httpx import AsyncClient

from ovejitas.features.asset.models import AssetKind, AssetMode
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit
from tests.conftest import AuthedUser
from tests.factories import AssetFactory, EventFactory

# 10-day window: 2026-06-01 .. 2026-06-10 inclusive (midnight date_to rolls to
# the next midnight → 10 whole days).
JUNE = {"date_from": "2026-06-01T00:00:00Z", "date_to": "2026-06-10T00:00:00Z"}
BEFORE = datetime(2026, 5, 15, tzinfo=UTC)


def _url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/reports/production-productivity"


async def _asset(farm_id: int, kind: AssetKind, name: str) -> int:
    asset = await AssetFactory.create_async(
        farm_id=farm_id, kind=kind, mode=AssetMode.AGGREGATED, name=name
    )
    return int(asset.id)


async def _head(
    farm_id: int,
    asset_id: int,
    user_id: int,
    adjustment: InventoryAdjustment,
    qty: str,
    when: datetime,
) -> None:
    await EventFactory.create_async(
        farm_id=farm_id,
        asset_id=asset_id,
        created_by=user_id,
        type=EventType.INVENTORY,
        adjustment=adjustment,
        quantity=Decimal(qty),
        unit=Unit.HEAD,
        occurred_at=when,
    )


async def _produce(
    farm_id: int, asset_id: int, user_id: int, category_id: int, qty: str, unit: str
) -> None:
    await EventFactory.create_async(
        farm_id=farm_id,
        asset_id=asset_id,
        created_by=user_id,
        type=EventType.PRODUCTION,
        category_id=category_id,
        quantity=Decimal(qty),
        unit=unit,
        occurred_at=datetime(2026, 6, 5, 9, 0, tzinfo=UTC),
    )


async def _category(
    client: AsyncClient, authed: AuthedUser, unit: str, name: str = "Huevos"
) -> int:
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/event-categories",
        headers=authed.headers,
        json={"type": "production", "name": name, "unit": unit},
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _target(
    client: AsyncClient, authed: AuthedUser, asset_id: int, category_id: int, **over: object
) -> None:
    body: dict[str, object] = {
        "asset_id": asset_id,
        "category_id": category_id,
        "basis": "per_head_continuous",
        "expected_rate": "0.8",
        "period": "day",
        "effective_from": "2026-01-01",
    }
    body.update(over)
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/production-targets", headers=authed.headers, json=body
    )
    assert resp.status_code == 201, resp.text


class TestProductionProductivity:
    async def test_per_head_continuous_percentage(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        farm, user = authed_user.farm_id, authed_user.user_id
        coop = await _asset(farm, AssetKind.ANIMAL, "Gallinas")
        cat = await _category(client, authed_user, "unit")
        await _target(client, authed_user, coop, cat)
        await _head(farm, coop, user, InventoryAdjustment.INCREMENT, "10", BEFORE)
        await _produce(farm, coop, user, cat, "64", "unit")

        resp = await client.get(_url(farm), headers=authed_user.headers, params=JUNE)

        assert resp.status_code == 200, resp.text
        row = resp.json()["data"][0]
        assert Decimal(row["produced"]) == Decimal("64")
        assert Decimal(row["expected"]) == Decimal("80")  # 0.8 x (10 head x 10 days)
        assert Decimal(row["productivity_pct"]) == Decimal("80.0")
        assert row["missing_capacity"] is False

    async def test_headcount_change_is_time_weighted(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        farm, user = authed_user.farm_id, authed_user.user_id
        coop = await _asset(farm, AssetKind.ANIMAL, "Gallinas")
        cat = await _category(client, authed_user, "unit")
        await _target(client, authed_user, coop, cat)
        await _head(farm, coop, user, InventoryAdjustment.INCREMENT, "10", BEFORE)
        # drop to 5 head at the window's midpoint: 10 head x 5d + 5 head x 5d = 75
        await _head(
            farm, coop, user, InventoryAdjustment.DECREMENT, "5", datetime(2026, 6, 6, tzinfo=UTC)
        )
        await _produce(farm, coop, user, cat, "60", "unit")

        resp = await client.get(_url(farm), headers=authed_user.headers, params=JUNE)

        row = resp.json()["data"][0]
        assert Decimal(row["expected"]) == Decimal("60")  # 0.8 x 75 animal-days
        assert Decimal(row["productivity_pct"]) == Decimal("100.0")

    async def test_dozen_converted_to_product_unit(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        farm, user = authed_user.farm_id, authed_user.user_id
        coop = await _asset(farm, AssetKind.ANIMAL, "Gallinas")
        cat = await _category(client, authed_user, "unit")
        await _target(client, authed_user, coop, cat)
        await _head(farm, coop, user, InventoryAdjustment.INCREMENT, "10", BEFORE)
        await _produce(farm, coop, user, cat, "5", "dozen")  # 60 eggs

        resp = await client.get(_url(farm), headers=authed_user.headers, params=JUNE)

        row = resp.json()["data"][0]
        assert Decimal(row["produced"]) == Decimal("60")
        assert Decimal(row["productivity_pct"]) == Decimal("75.0")  # 60 / 80

    async def test_per_event_basis(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        farm, user = authed_user.farm_id, authed_user.user_id
        flock = await _asset(farm, AssetKind.ANIMAL, "Ovejas")
        cat = await _category(client, authed_user, "kg", name="Lana")
        await _target(
            client, authed_user, flock, cat, basis="per_event", period=None, expected_rate="3"
        )
        await _produce(farm, flock, user, cat, "2", "kg")
        await _produce(farm, flock, user, cat, "4", "kg")

        resp = await client.get(_url(farm), headers=authed_user.headers, params=JUNE)

        row = resp.json()["data"][0]
        assert Decimal(row["produced"]) == Decimal("6")
        assert Decimal(row["expected"]) == Decimal("6")  # 3 x 2 events
        assert Decimal(row["productivity_pct"]) == Decimal("100.0")

    async def test_total_basis_on_crop(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        farm, user = authed_user.farm_id, authed_user.user_id
        field = await _asset(farm, AssetKind.CROP, "Maíz")
        cat = await _category(client, authed_user, "kg", name="Grano")
        await _target(
            client, authed_user, field, cat, basis="total", period=None, expected_rate="500"
        )
        await _produce(farm, field, user, cat, "480", "kg")

        resp = await client.get(_url(farm), headers=authed_user.headers, params=JUNE)

        row = resp.json()["data"][0]
        assert Decimal(row["expected"]) == Decimal("500")
        assert Decimal(row["productivity_pct"]) == Decimal("96.0")

    async def test_produced_without_target_flags_missing_capacity(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        farm, user = authed_user.farm_id, authed_user.user_id
        coop = await _asset(farm, AssetKind.ANIMAL, "Gallinas")
        cat = await _category(client, authed_user, "unit")
        await _produce(farm, coop, user, cat, "30", "unit")

        resp = await client.get(_url(farm), headers=authed_user.headers, params=JUNE)

        row = resp.json()["data"][0]
        assert Decimal(row["produced"]) == Decimal("30")
        assert row["expected"] is None
        assert row["missing_capacity"] is True

    async def test_missing_window_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.get(_url(authed_user.farm_id), headers=authed_user.headers)
        assert resp.status_code == 422
