"""Production-productivity report — produced vs expected per (asset, product).

Headcount is time-weighted (animal-days) with arrivals and departures snapped to
whole farm-local days, so HEAD inventory is inserted with an explicit occurred_at
before the window; production events carry a category_id.
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

    async def test_in_progress_day_expects_a_whole_day_not_prorated_hours(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        # date_to is "now" mid-afternoon (an in-progress day), not midnight. The
        # day must still count as a whole day: 1.0 x (1000 head x 1 day) = 1000,
        # not prorated to the ~13.75 elapsed hours.
        farm, user = authed_user.farm_id, authed_user.user_id
        coop = await _asset(farm, AssetKind.ANIMAL, "Gallinas")
        cat = await _category(client, authed_user, "unit")
        await _target(client, authed_user, coop, cat, expected_rate="1.0")
        await _head(farm, coop, user, InventoryAdjustment.INCREMENT, "1000", BEFORE)
        await _produce(farm, coop, user, cat, "500", "unit")

        params = {"date_from": "2026-06-05T00:00:00Z", "date_to": "2026-06-05T13:45:00Z"}
        resp = await client.get(_url(farm), headers=authed_user.headers, params=params)

        assert resp.status_code == 200, resp.text
        row = resp.json()["data"][0]
        assert Decimal(row["expected"]) == Decimal("1000")

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

    async def test_rate_change_is_time_weighted_across_targets(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        farm, user = authed_user.farm_id, authed_user.user_id
        coop = await _asset(farm, AssetKind.ANIMAL, "Gallinas")
        cat = await _category(client, authed_user, "unit")
        # 0.8/day through Jun 5, then 0.6/day from Jun 6 — an effective-dated change.
        await _target(
            client, authed_user, coop, cat, effective_from="2026-01-01", effective_to="2026-06-05"
        )
        await _target(
            client, authed_user, coop, cat, expected_rate="0.6", effective_from="2026-06-06"
        )
        await _head(farm, coop, user, InventoryAdjustment.INCREMENT, "10", BEFORE)
        await _produce(farm, coop, user, cat, "70", "unit")

        resp = await client.get(_url(farm), headers=authed_user.headers, params=JUNE)

        row = resp.json()["data"][0]
        # 0.8 x (10 head x 5 days) + 0.6 x (10 head x 5 days) = 40 + 30
        assert Decimal(row["expected"]) == Decimal("70")
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


async def _set_timezone(client: AsyncClient, authed: AuthedUser, name: str) -> None:
    resp = await client.patch(
        f"/api/v1/farms/{authed.farm_id}", headers=authed.headers, json={"timezone": name}
    )
    assert resp.status_code == 200, resp.text


# 10 whole local days, 2026-06-01 .. 2026-06-10 on the farm's calendar.
LOCAL_JUNE = {"date_from": "2026-06-01", "date_to": "2026-06-10"}


class TestTargetDatesAreFarmLocal:
    """``effective_from``/``effective_to`` are bare calendar dates: a farmer
    saying "from the 6th" means the 6th where the animals are. Read as UTC
    midnight they start the rate three hours early at UTC-3."""

    async def _coop_with_target(
        self, client: AsyncClient, authed: AuthedUser, effective_from: str
    ) -> None:
        farm, user = authed.farm_id, authed.user_id
        await _set_timezone(client, authed, "America/Montevideo")
        coop = await _asset(farm, AssetKind.ANIMAL, "Gallinas")
        cat = await _category(client, authed, "unit")
        await _target(client, authed, coop, cat, expected_rate="1.0", effective_from=effective_from)
        await _head(farm, coop, user, InventoryAdjustment.INCREMENT, "10", BEFORE)

    async def test_target_starting_mid_window_bills_whole_local_days(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await self._coop_with_target(client, authed_user, "2026-06-06")

        resp = await client.get(
            _url(authed_user.farm_id), headers=authed_user.headers, params=LOCAL_JUNE
        )

        assert resp.status_code == 200, resp.text
        # 1.0 x (10 head x 5 whole local days) = 50 — not 51.25, which is what
        # a UTC-midnight reading of the 6th would bill (5 days + 3 hours).
        assert Decimal(resp.json()["data"][0]["expected"]) == Decimal("50")

    async def test_target_starting_on_the_windows_last_local_day_still_applies(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await self._coop_with_target(client, authed_user, "2026-06-10")

        resp = await client.get(
            _url(authed_user.farm_id), headers=authed_user.headers, params=LOCAL_JUNE
        )

        assert resp.status_code == 200, resp.text
        row = resp.json()["data"][0]
        assert row["missing_capacity"] is False
        assert Decimal(row["expected"]) == Decimal("10")  # 1.0 x (10 head x 1 day)


class TestWindowStartIsTheStartOfTheDay:
    """A day-grained report asked about "today" must expect a whole day's goal,
    whatever time of day the question is asked."""

    async def _flock_of_500(self, client: AsyncClient, authed: AuthedUser) -> tuple[int, int]:
        farm, user = authed.farm_id, authed.user_id
        coop = await _asset(farm, AssetKind.ANIMAL, "Gallinas")
        cat = await _category(client, authed, "unit")
        await _target(client, authed, coop, cat, expected_rate="1.0")
        await _head(farm, coop, user, InventoryAdjustment.INCREMENT, "500", BEFORE)
        return coop, cat

    async def test_whole_date_bounds_expect_the_full_flock(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await self._flock_of_500(client, authed_user)

        resp = await client.get(
            _url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"date_from": "2026-06-05", "date_to": "2026-06-05"},
        )

        assert Decimal(resp.json()["data"][0]["expected"]) == Decimal("500")

    async def test_asking_late_in_the_day_still_expects_the_full_flock(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await self._flock_of_500(client, authed_user)

        resp = await client.get(
            _url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"date_from": "2026-06-05T18:45:00Z", "date_to": "2026-06-05T18:45:00Z"},
        )

        assert Decimal(resp.json()["data"][0]["expected"]) == Decimal("500")

    async def test_asking_late_in_the_day_counts_the_mornings_production(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        """Numerator and denominator cover the same days. Bounding produced at
        the raw date_from would drop this morning's eggs while still expecting
        the whole day's goal, reporting a healthy flock at 0%."""
        coop, cat = await self._flock_of_500(client, authed_user)
        await _produce(authed_user.farm_id, coop, authed_user.user_id, cat, "400", "unit")

        resp = await client.get(
            _url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"date_from": "2026-06-05T18:45:00Z", "date_to": "2026-06-05T18:45:00Z"},
        )

        row = resp.json()["data"][0]
        assert Decimal(row["produced"]) == Decimal("400")  # logged 09:00, before the ask
        assert Decimal(row["productivity_pct"]) == Decimal("80.0")


# One whole local day, 2026-06-05, on the farm's calendar.
LOCAL_DAY = {"date_from": "2026-06-05", "date_to": "2026-06-05"}


class TestArrivalCoversItsWholeDay:
    """Head joining a flock count from the start of their farm-local day,
    whether they establish it or join an existing pool."""

    async def _coop(self, client: AsyncClient, authed: AuthedUser) -> int:
        coop = await _asset(authed.farm_id, AssetKind.ANIMAL, "Gallinas")
        cat = await _category(client, authed, "unit")
        await _target(client, authed, coop, cat, expected_rate="1.0")
        return coop

    async def test_flock_acquired_late_in_the_day_expects_a_whole_day(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        farm, user = authed_user.farm_id, authed_user.user_id
        coop = await self._coop(client, authed_user)
        await _head(
            farm,
            coop,
            user,
            InventoryAdjustment.INCREMENT,
            "500",
            datetime(2026, 6, 5, 18, 45, tzinfo=UTC),
        )

        resp = await client.get(_url(farm), headers=authed_user.headers, params=LOCAL_DAY)

        assert resp.status_code == 200, resp.text
        # 1.0 x (500 head x 1 whole day) = 500 — not 109.375, the 5¼ hours that
        # remained after the flock arrived.
        assert Decimal(resp.json()["data"][0]["expected"]) == Decimal("500")

    async def test_a_second_lot_the_same_day_also_covers_the_whole_day(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        farm, user = authed_user.farm_id, authed_user.user_id
        coop = await self._coop(client, authed_user)
        await _head(
            farm,
            coop,
            user,
            InventoryAdjustment.INCREMENT,
            "300",
            datetime(2026, 6, 5, 9, tzinfo=UTC),
        )
        await _head(
            farm,
            coop,
            user,
            InventoryAdjustment.INCREMENT,
            "200",
            datetime(2026, 6, 5, 18, 45, tzinfo=UTC),
        )

        resp = await client.get(_url(farm), headers=authed_user.headers, params=LOCAL_DAY)

        assert resp.status_code == 200, resp.text
        # Both lots open the day they arrived, so the coop is owed a full day
        # for all 500 head — not the 343.75 that prorating the 18:45 lot gives.
        assert Decimal(resp.json()["data"][0]["expected"]) == Decimal("500")

    async def test_the_whole_day_is_the_farms_day_not_utcs(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        farm, user = authed_user.farm_id, authed_user.user_id
        await _set_timezone(client, authed_user, "America/Montevideo")
        coop = await self._coop(client, authed_user)
        # 22:30 on the 5th in Montevideo — already the 6th in UTC.
        await _head(
            farm,
            coop,
            user,
            InventoryAdjustment.INCREMENT,
            "500",
            datetime(2026, 6, 6, 1, 30, tzinfo=UTC),
        )

        resp = await client.get(_url(farm), headers=authed_user.headers, params=LOCAL_DAY)

        assert resp.status_code == 200, resp.text
        # Flooring to UTC midnight would open the flock at 21:00 local on the
        # 5th and bill 3 of the window's hours: 62.5.
        assert Decimal(resp.json()["data"][0]["expected"]) == Decimal("500")


class TestDepartureCoversItsWholeDay:
    """Animals sold or lost count for the day they left, matching the production
    already credited to them that morning."""

    async def _coop_of_10(self, client: AsyncClient, authed: AuthedUser) -> int:
        coop = await _asset(authed.farm_id, AssetKind.ANIMAL, "Gallinas")
        cat = await _category(client, authed, "unit")
        await _target(client, authed, coop, cat, expected_rate="1.0")
        await _head(
            authed.farm_id, coop, authed.user_id, InventoryAdjustment.INCREMENT, "10", BEFORE
        )
        return coop

    async def test_a_sale_mid_morning_still_counts_that_day(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        farm, user = authed_user.farm_id, authed_user.user_id
        coop = await self._coop_of_10(client, authed_user)
        await _head(
            farm,
            coop,
            user,
            InventoryAdjustment.DECREMENT,
            "5",
            datetime(2026, 6, 6, 8, 0, tzinfo=UTC),
        )

        resp = await client.get(_url(farm), headers=authed_user.headers, params=JUNE)

        assert resp.status_code == 200, resp.text
        # 10 head through the end of the 6th (6 days) + 5 head for the 7th-10th
        # (4 days) = 80. Prorating to 08:00 would give 78.33.
        assert Decimal(resp.json()["data"][0]["expected"]) == Decimal("80")

    async def test_a_departure_exactly_at_midnight_does_not_gain_a_day(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        """The ceiling is a true one. An animal gone at 00:00:00 was present for
        none of the day that instant opened, and every other bound in this
        report is half-open the same way."""
        farm, user = authed_user.farm_id, authed_user.user_id
        coop = await self._coop_of_10(client, authed_user)
        await _head(
            farm, coop, user, InventoryAdjustment.DECREMENT, "5", datetime(2026, 6, 6, tzinfo=UTC)
        )

        resp = await client.get(_url(farm), headers=authed_user.headers, params=JUNE)

        assert resp.status_code == 200, resp.text
        # 10 head x 5d + 5 head x 5d = 75 — the 6th is not granted to the five
        # that left as it began.
        assert Decimal(resp.json()["data"][0]["expected"]) == Decimal("75")

    async def test_a_later_increment_covers_its_whole_day(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        """Arrivals and departures are both whole-day facts, so a lot joining an
        existing pool opens its day exactly as the establishing lot does."""
        farm, user = authed_user.farm_id, authed_user.user_id
        coop = await self._coop_of_10(client, authed_user)
        await _head(
            farm,
            coop,
            user,
            InventoryAdjustment.INCREMENT,
            "10",
            datetime(2026, 6, 6, 18, 0, tzinfo=UTC),
        )

        resp = await client.get(_url(farm), headers=authed_user.headers, params=JUNE)

        assert resp.status_code == 200, resp.text
        # 10 head x 5d (1st-5th) + 20 head x 5d (6th-10th) = 50 + 100 = 150
        assert Decimal(resp.json()["data"][0]["expected"]) == Decimal("150")

    async def test_a_sale_after_a_same_day_purchase_is_ordered_correctly(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        """Shifting moves rows both ways and can carry one past another, so the
        stream is re-sorted before integrating — otherwise the cursor walks
        backwards."""
        farm, user = authed_user.farm_id, authed_user.user_id
        coop = await self._coop_of_10(client, authed_user)
        # Sold at 08:00 (moves forward to the 7th), bought more at 18:00 (moves
        # back to the 6th) — the raw order is the reverse of the effective one.
        await _head(
            farm,
            coop,
            user,
            InventoryAdjustment.DECREMENT,
            "5",
            datetime(2026, 6, 6, 8, 0, tzinfo=UTC),
        )
        await _head(
            farm,
            coop,
            user,
            InventoryAdjustment.INCREMENT,
            "20",
            datetime(2026, 6, 6, 18, 0, tzinfo=UTC),
        )

        resp = await client.get(_url(farm), headers=authed_user.headers, params=JUNE)

        assert resp.status_code == 200, resp.text
        # 10 head x 5d (1st-5th) + 30 x 1d (the 6th, both lots present)
        # + 25 x 4d (7th-10th) = 50 + 30 + 100 = 180
        assert Decimal(resp.json()["data"][0]["expected"]) == Decimal("180")

    async def test_a_flock_bought_and_sold_the_same_day_counts_that_day(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        farm, user = authed_user.farm_id, authed_user.user_id
        coop = await _asset(farm, AssetKind.ANIMAL, "Gallinas")
        cat = await _category(client, authed_user, "unit")
        await _target(client, authed_user, coop, cat, expected_rate="1.0")
        await _head(
            farm,
            coop,
            user,
            InventoryAdjustment.INCREMENT,
            "500",
            datetime(2026, 6, 5, 9, tzinfo=UTC),
        )
        await _head(
            farm,
            coop,
            user,
            InventoryAdjustment.DECREMENT,
            "500",
            datetime(2026, 6, 5, 15, tzinfo=UTC),
        )

        resp = await client.get(_url(farm), headers=authed_user.headers, params=LOCAL_DAY)

        assert resp.status_code == 200, resp.text
        # Arrival opens the day, departure closes it — the same whole day an
        # individually-tracked animal bought and sold that day would get.
        assert Decimal(resp.json()["data"][0]["expected"]) == Decimal("500")


class TestResetKeepsItsInstant:
    """A RESET is the one adjustment whose direction the row does not reveal: it
    sets the count absolutely, so whether it is a rise or a fall depends on the
    running balance. Rather than guess between the floor and the ceil, it stays
    where it was recorded."""

    async def test_a_reset_is_not_moved_to_a_day_boundary(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        farm, user = authed_user.farm_id, authed_user.user_id
        coop = await _asset(farm, AssetKind.ANIMAL, "Gallinas")
        cat = await _category(client, authed_user, "unit")
        await _target(client, authed_user, coop, cat, expected_rate="1.0")
        await _head(farm, coop, user, InventoryAdjustment.INCREMENT, "10", BEFORE)
        await _head(
            farm,
            coop,
            user,
            InventoryAdjustment.RESET,
            "20",
            datetime(2026, 6, 6, 12, tzinfo=UTC),
        )

        resp = await client.get(_url(farm), headers=authed_user.headers, params=JUNE)

        assert resp.status_code == 200, resp.text
        # 10 head x 5.5d + 20 head x 4.5d = 55 + 90 = 145. Flooring the reset
        # would give 150, ceiling it 140.
        assert Decimal(resp.json()["data"][0]["expected"]) == Decimal("145")
