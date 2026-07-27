"""Production-productivity for individually-tracked herds.

An individual-mode asset records headcount as one row per animal, not as HEAD
inventory events, so the report reads presence intervals instead of a level
integral. Both ends land on whole farm-local days: an animal counts from the
start of the day it arrived through the end of the day it left.
"""

from datetime import UTC, datetime
from decimal import Decimal

from httpx import AsyncClient

from ovejitas.features.asset.models import AssetKind, AssetMode
from ovejitas.features.event.types import EventType
from tests.conftest import AuthedUser
from tests.factories import AssetFactory, EventFactory

# 10-day window: 2026-06-01 .. 2026-06-10 inclusive.
JUNE = {"date_from": "2026-06-01T00:00:00Z", "date_to": "2026-06-10T00:00:00Z"}
# One whole local day on the farm's calendar.
LOCAL_DAY = {"date_from": "2026-06-05", "date_to": "2026-06-05"}
BEFORE = "2026-05-15T00:00:00Z"


def _url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/reports/production-productivity"


async def _herd(farm_id: int, mode: AssetMode = AssetMode.INDIVIDUAL) -> int:
    asset = await AssetFactory.create_async(
        farm_id=farm_id, kind=AssetKind.ANIMAL, mode=mode, name="Vacas"
    )
    return int(asset.id)


async def _category(client: AsyncClient, authed: AuthedUser) -> int:
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/event-categories",
        headers=authed.headers,
        json={"type": "production", "name": "Leche", "unit": "l"},
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _target(client: AsyncClient, authed: AuthedUser, asset_id: int, category_id: int) -> None:
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/production-targets",
        headers=authed.headers,
        json={
            "asset_id": asset_id,
            "category_id": category_id,
            "basis": "per_head_continuous",
            "expected_rate": "1.0",
            "period": "day",
            "effective_from": "2026-01-01",
        },
    )
    assert resp.status_code == 201, resp.text


async def _cow(
    client: AsyncClient, authed: AuthedUser, asset_id: int, tag: str, acquired_at: str
) -> int:
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/assets/{asset_id}/individuals",
        headers=authed.headers,
        json={"tag": tag, "acquisition_method": "other", "acquired_at": acquired_at},
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _retire(
    client: AsyncClient,
    authed: AuthedUser,
    asset_id: int,
    cow_id: int,
    body: dict[str, object],
) -> None:
    resp = await client.patch(
        f"/api/v1/farms/{authed.farm_id}/assets/{asset_id}/individuals/{cow_id}",
        headers=authed.headers,
        json=body,
    )
    assert resp.status_code == 200, resp.text


async def _milk(farm_id: int, asset_id: int, user_id: int, category_id: int, qty: str) -> None:
    await EventFactory.create_async(
        farm_id=farm_id,
        asset_id=asset_id,
        created_by=user_id,
        type=EventType.PRODUCTION,
        category_id=category_id,
        quantity=Decimal(qty),
        unit="l",
        occurred_at=datetime(2026, 6, 5, 9, 0, tzinfo=UTC),
    )


async def _expected(client: AsyncClient, authed: AuthedUser, params: dict[str, str]) -> Decimal:
    resp = await client.get(_url(authed.farm_id), headers=authed.headers, params=params)
    assert resp.status_code == 200, resp.text
    return Decimal(resp.json()["data"][0]["expected"])


class TestIndividualHerdHasHeadDays:
    """The defect: an individual-mode asset had no HEAD inventory events, so the
    denominator summed nothing and every such herd reported a dead report."""

    async def test_a_cow_acquired_before_the_window_counts_every_day(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        farm, user = authed_user.farm_id, authed_user.user_id
        herd = await _herd(farm)
        cat = await _category(client, authed_user)
        await _target(client, authed_user, herd, cat)
        await _cow(client, authed_user, herd, "COW-1", BEFORE)
        await _milk(farm, herd, user, cat, "8")

        resp = await client.get(_url(farm), headers=authed_user.headers, params=JUNE)

        assert resp.status_code == 200, resp.text
        row = resp.json()["data"][0]
        # 1.0 x (1 head x 10 days) = 10 — was 0.00, with a null percentage.
        assert Decimal(row["expected"]) == Decimal("10")
        assert Decimal(row["produced"]) == Decimal("8")
        assert Decimal(row["productivity_pct"]) == Decimal("80.0")

    async def test_a_cow_still_active_is_present_through_the_window_end(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        herd = await _herd(authed_user.farm_id)
        cat = await _category(client, authed_user)
        await _target(client, authed_user, herd, cat)
        await _cow(client, authed_user, herd, "COW-1", "2026-06-06T00:00:00Z")

        # Arrived on the 6th, never left: the 6th through the 10th = 5 days.
        assert await _expected(client, authed_user, JUNE) == Decimal("5")

    async def test_a_born_calf_counts_from_its_birth_day(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        # A birth emits its own ACQUISITION(born) event, so offspring join the
        # denominator the same way a purchase does.
        farm = authed_user.farm_id
        herd = await _herd(farm)
        cat = await _category(client, authed_user)
        await _target(client, authed_user, herd, cat)
        mother = await _cow(client, authed_user, herd, "COW-1", BEFORE)
        resp = await client.post(
            f"/api/v1/farms/{farm}/assets/{herd}/individuals/{mother}/births",
            headers=authed_user.headers,
            json={
                "occurred_at": "2026-06-06T10:00:00Z",
                "offspring": [{"tag": "CALF-1"}],
            },
        )
        assert resp.status_code == 201, resp.text

        # Mother 10 days + calf from the 6th (whole day) through the 10th = 5.
        assert await _expected(client, authed_user, JUNE) == Decimal("15")


class TestArrivalCoversItsWholeDay:
    async def test_a_cow_acquired_late_in_the_day_expects_a_whole_day(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        herd = await _herd(authed_user.farm_id)
        cat = await _category(client, authed_user)
        await _target(client, authed_user, herd, cat)
        await _cow(client, authed_user, herd, "COW-1", "2026-06-05T18:45:00Z")

        assert await _expected(client, authed_user, LOCAL_DAY) == Decimal("1")

    async def test_a_herd_onboarded_the_same_afternoon_counts_every_animal(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        """Unlike a flock, where one event carries all 500 head, a herd is one
        arrival per animal — so every arrival floors, not just the first."""
        herd = await _herd(authed_user.farm_id)
        cat = await _category(client, authed_user)
        await _target(client, authed_user, herd, cat)
        for n in range(30):
            await _cow(client, authed_user, herd, f"COW-{n}", "2026-06-05T18:45:00Z")

        # 30 cow-days, not the ~1.2 that prorating 30 arrivals to 5 1/4 hours gives.
        assert await _expected(client, authed_user, LOCAL_DAY) == Decimal("30")


class TestDepartureCoversItsWholeDay:
    async def test_a_cow_sold_mid_window_counts_the_day_she_left(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        herd = await _herd(authed_user.farm_id)
        cat = await _category(client, authed_user)
        await _target(client, authed_user, herd, cat)
        cow = await _cow(client, authed_user, herd, "COW-1", BEFORE)
        await _retire(
            client,
            authed_user,
            herd,
            cow,
            {"status": "sold", "sold_at": "2026-06-06T08:00:00Z", "sale_amount": "500"},
        )

        # The 1st through the end of the 6th = 6 whole days, not 5.33.
        assert await _expected(client, authed_user, JUNE) == Decimal("6")

    async def test_a_cow_that_died_mid_window_counts_the_day_she_died(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        herd = await _herd(authed_user.farm_id)
        cat = await _category(client, authed_user)
        await _target(client, authed_user, herd, cat)
        cow = await _cow(client, authed_user, herd, "COW-1", BEFORE)
        await _retire(
            client,
            authed_user,
            herd,
            cow,
            {"status": "deceased", "died_at": "2026-06-06T08:00:00Z", "cause": "illness"},
        )

        assert await _expected(client, authed_user, JUNE) == Decimal("6")

    async def test_a_cow_gone_before_the_window_contributes_nothing(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        herd = await _herd(authed_user.farm_id)
        cat = await _category(client, authed_user)
        await _target(client, authed_user, herd, cat)
        cow = await _cow(client, authed_user, herd, "COW-1", BEFORE)
        await _retire(
            client,
            authed_user,
            herd,
            cow,
            {"status": "sold", "sold_at": "2026-05-20T08:00:00Z", "sale_amount": "500"},
        )

        assert await _expected(client, authed_user, JUNE) == Decimal("0")


class TestAggregatedAssetsAreUnaffected:
    async def test_a_flock_still_reads_its_inventory_stream(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        """Regression guard on the branch: an aggregated asset must keep using
        the HEAD integral, and must not pick up individual rows."""
        farm = authed_user.farm_id
        coop = await _herd(farm, mode=AssetMode.AGGREGATED)
        cat = await _category(client, authed_user)
        await _target(client, authed_user, coop, cat)
        resp = await client.post(
            f"/api/v1/farms/{farm}/assets/{coop}/flock/acquisitions",
            headers=authed_user.headers,
            json={"quantity": 10, "occurred_at": BEFORE},
        )
        assert resp.status_code == 201, resp.text

        assert await _expected(client, authed_user, JUNE) == Decimal("100")
