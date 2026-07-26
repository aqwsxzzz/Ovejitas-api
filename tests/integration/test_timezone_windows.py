"""Date windows are drawn on the farm's calendar, not UTC's.

The pivot event sits at 23:30 in Montevideo (UTC-3), which is already the next
day in UTC. Every test here turns on which side of a day boundary it lands.
"""

from datetime import UTC, datetime
from decimal import Decimal

from httpx import AsyncClient

from ovejitas.features.event.types import EventType
from tests.conftest import AuthedUser
from tests.factories import AssetFactory, EventFactory, currency_id_for

# 2026-04-10 23:30 in Montevideo is 2026-04-11 02:30 UTC.
LATE_LOCAL_EVENING = datetime(2026, 4, 11, 2, 30, tzinfo=UTC)


async def _set_timezone(client: AsyncClient, user: AuthedUser, name: str) -> None:
    resp = await client.patch(
        f"/api/v1/farms/{user.farm_id}",
        headers=user.headers,
        json={"timezone": name},
    )
    assert resp.status_code == 200, resp.text


async def _asset_with_late_event(user: AuthedUser, **event_kw: object) -> int:
    asset = await AssetFactory.create_async(farm_id=user.farm_id)
    await EventFactory.create_async(
        farm_id=user.farm_id,
        asset_id=asset.id,
        created_by=user.user_id,
        occurred_at=LATE_LOCAL_EVENING,
        **event_kw,
    )
    return int(asset.id)


async def _list_events(client: AsyncClient, user: AuthedUser, asset_id: int, **params: str) -> int:
    resp = await client.get(
        f"/api/v1/farms/{user.farm_id}/assets/{asset_id}/events",
        headers=user.headers,
        params=params,
    )
    assert resp.status_code == 200, resp.text
    total: int = resp.json()["meta"]["total"]
    return total


# Four instants straddling both edges of the local day 2026-04-10 (UTC-3).
STRADDLING_LOCAL_DAY = [
    datetime(2026, 4, 10, 2, 30, tzinfo=UTC),  # 09th 23:30 local — before
    datetime(2026, 4, 10, 3, 15, tzinfo=UTC),  # 10th 00:15 local — inside
    datetime(2026, 4, 11, 2, 30, tzinfo=UTC),  # 10th 23:30 local — inside
    datetime(2026, 4, 11, 3, 15, tzinfo=UTC),  # 11th 00:15 local — after
]


async def _asset_spanning_the_day_edges(user: AuthedUser) -> int:
    asset = await AssetFactory.create_async(farm_id=user.farm_id)
    for when in STRADDLING_LOCAL_DAY:
        await EventFactory.create_async(
            farm_id=user.farm_id,
            asset_id=asset.id,
            created_by=user.user_id,
            occurred_at=when,
        )
    return int(asset.id)


class TestSameDateOnBothBoundsIsOneCleanDay:
    async def test_matching_date_bounds_select_exactly_one_local_day(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await _set_timezone(client, authed_user, "America/Montevideo")
        asset_id = await _asset_spanning_the_day_edges(authed_user)

        total = await _list_events(
            client, authed_user, asset_id, date_from="2026-04-10", date_to="2026-04-10"
        )

        assert total == 2

    async def test_an_explicit_instant_lower_bound_is_not_floored_to_its_day(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        """Only midnight means 'whole day'. A bound carrying a time is exact, so
        mixing an instant with a date is the caller's choice, not a rounding."""
        await _set_timezone(client, authed_user, "America/Montevideo")
        asset_id = await _asset_spanning_the_day_edges(authed_user)

        total = await _list_events(
            client,
            authed_user,
            asset_id,
            date_from="2026-04-10T12:00:00",
            date_to="2026-04-10",
        )

        assert total == 1


class TestListWindowFollowsFarmCalendar:
    async def test_naive_date_to_includes_late_local_evening(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await _set_timezone(client, authed_user, "America/Montevideo")
        asset_id = await _asset_with_late_event(authed_user)

        total = await _list_events(client, authed_user, asset_id, date_to="2026-04-10")

        assert total == 1

    async def test_naive_date_from_on_next_local_day_excludes_it(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await _set_timezone(client, authed_user, "America/Montevideo")
        asset_id = await _asset_with_late_event(authed_user)

        total = await _list_events(client, authed_user, asset_id, date_from="2026-04-11")

        assert total == 0

    async def test_naive_date_to_on_a_utc_farm_excludes_it(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        """The default UTC farm still splits days at UTC midnight — proving the
        boundary really comes from the farm's zone rather than a fixed offset."""
        asset_id = await _asset_with_late_event(authed_user)

        total = await _list_events(client, authed_user, asset_id, date_to="2026-04-10")

        assert total == 0

    async def test_aware_date_to_keeps_the_instant_it_names(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        """An explicit offset names an exact instant and is never re-anchored."""
        await _set_timezone(client, authed_user, "America/Montevideo")
        asset_id = await _asset_with_late_event(authed_user)

        total = await _list_events(client, authed_user, asset_id, date_to="2026-04-11T01:00:00Z")

        assert total == 0


class TestReportWindowFollowsFarmCalendar:
    async def test_profitability_naive_date_to_includes_late_local_evening(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await _set_timezone(client, authed_user, "America/Montevideo")
        await _asset_with_late_event(
            authed_user,
            type=EventType.INCOME,
            amount=Decimal("100"),
            currency_id=await currency_id_for(authed_user.farm_id, "USD"),
            quantity=None,
            unit=None,
        )

        resp = await client.get(
            f"/api/v1/farms/{authed_user.farm_id}/reports/profitability",
            headers=authed_user.headers,
            params={"date_to": "2026-04-10"},
        )

        assert resp.status_code == 200, resp.text
        assert Decimal(resp.json()["data"][0]["income_total"]) == Decimal("100")


# 2026-04-10 10:00 and 23:30 in Montevideo — one local day, two UTC days.
MORNING_LOCAL = datetime(2026, 4, 10, 13, tzinfo=UTC)


async def _aggregate_buckets(
    client: AsyncClient, user: AuthedUser, **params: str
) -> list[dict[str, str]]:
    resp = await client.get(
        f"/api/v1/farms/{user.farm_id}/reports/aggregate",
        headers=user.headers,
        params={"type": "production", "bucket": "day", **params},
    )
    assert resp.status_code == 200, resp.text
    data: list[dict[str, str]] = resp.json()["data"]
    return data


class TestBucketsFollowFarmCalendar:
    async def _two_events_one_local_day(self, user: AuthedUser) -> None:
        asset = await AssetFactory.create_async(farm_id=user.farm_id)
        for when in (MORNING_LOCAL, LATE_LOCAL_EVENING):
            await EventFactory.create_async(
                farm_id=user.farm_id,
                asset_id=asset.id,
                created_by=user.user_id,
                occurred_at=when,
                type=EventType.PRODUCTION,
                quantity=Decimal("1"),
                unit="l",
            )

    async def test_day_bucket_groups_a_whole_local_day_into_one_row(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await _set_timezone(client, authed_user, "America/Montevideo")
        await self._two_events_one_local_day(authed_user)

        rows = await _aggregate_buckets(client, authed_user)

        assert len(rows) == 1
        assert Decimal(rows[0]["value"]) == Decimal("2")

    async def test_day_bucket_is_labelled_with_the_local_calendar_day(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await _set_timezone(client, authed_user, "America/Montevideo")
        await self._two_events_one_local_day(authed_user)

        rows = await _aggregate_buckets(client, authed_user)

        # The local day both events fall on — the later one is already the 11th
        # in UTC, and a plain date leaves no room to read it as such.
        assert rows[0]["bucket"] == "2026-04-10"

    async def test_day_bucket_round_trips_as_a_date_from_bound(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        """The label a client renders is also the filter that reselects it."""
        await _set_timezone(client, authed_user, "America/Montevideo")
        await self._two_events_one_local_day(authed_user)
        label = (await _aggregate_buckets(client, authed_user))[0]["bucket"]

        rows = await _aggregate_buckets(client, authed_user, date_from=label, date_to=label)

        assert len(rows) == 1
        assert Decimal(rows[0]["value"]) == Decimal("2")

    async def test_day_bucket_on_a_utc_farm_splits_the_local_day_in_two(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        """The same two events under UTC bucket separately — the grain really
        comes from the farm's zone rather than a fixed offset."""
        await self._two_events_one_local_day(authed_user)

        rows = await _aggregate_buckets(client, authed_user)

        assert len(rows) == 2
