"""Presence-interval overlap for the individual headcount branch (report.headcount).

``overlap_days`` is the pure half of that branch: given one animal's presence
interval it reports how much of the span that animal was here for. Every
edge that decides an animal-day is here, without a database.
"""

from datetime import UTC, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from ovejitas.features.report.productivity_math import Span, overlap_days

MONTEVIDEO = ZoneInfo("America/Montevideo")  # UTC-3 year-round, no DST ambiguity

# 2026-06-01 .. 2026-06-10 inclusive — 10 whole days.
JUNE = Span(
    start=datetime(2026, 6, 1, tzinfo=UTC),
    end=datetime(2026, 6, 11, tzinfo=UTC),
    tz=ZoneInfo("UTC"),
)


def _day(day: int) -> datetime:
    return datetime(2026, 6, day, tzinfo=UTC)


class TestOverlapDays:
    @pytest.mark.parametrize(
        "start, end, expected",
        [
            (_day(1), _day(11), "10"),
            (_day(6), _day(11), "5"),
            (_day(1), _day(6), "5"),
            (_day(4), _day(7), "3"),
            (datetime(2026, 5, 1, tzinfo=UTC), datetime(2026, 7, 1, tzinfo=UTC), "10"),
        ],
        ids=["exactly the span", "opens midway", "closes midway", "wholly inside", "engulfs"],
    )
    def test_counts_only_the_days_inside_the_span(
        self, start: datetime, end: datetime, expected: str
    ) -> None:
        assert overlap_days(start, end, JUNE) == Decimal(expected)

    @pytest.mark.parametrize(
        "start, end",
        [
            (datetime(2026, 4, 1, tzinfo=UTC), datetime(2026, 5, 1, tzinfo=UTC)),
            (datetime(2026, 7, 1, tzinfo=UTC), datetime(2026, 8, 1, tzinfo=UTC)),
            (_day(5), _day(5)),
        ],
        ids=["ends before the span", "starts after the span", "empty interval"],
    )
    def test_disjoint_presence_contributes_nothing(self, start: datetime, end: datetime) -> None:
        assert overlap_days(start, end, JUNE) == Decimal(0)

    def test_presence_touching_only_the_spans_open_bound_contributes_nothing(self) -> None:
        # The span is half-open, so an animal that left exactly at its start
        # was never inside it.
        assert overlap_days(datetime(2026, 5, 20, tzinfo=UTC), _day(1), JUNE) == Decimal(0)

    def test_a_part_day_is_a_fraction(self) -> None:
        # overlap_days itself does no day-rounding — the caller floors arrivals
        # and ceils departures before handing intervals over.
        assert overlap_days(datetime(2026, 6, 1, 18, tzinfo=UTC), _day(2), JUNE) == Decimal("0.25")


class TestSpanOnTheFarmsCalendar:
    def test_a_local_day_span_is_offset_from_the_utc_one(self) -> None:
        # 2026-06-05 in Montevideo runs 03:00Z to 03:00Z, not midnight to midnight.
        local_day = Span(
            start=datetime(2026, 6, 5, tzinfo=MONTEVIDEO),
            end=datetime(2026, 6, 6, tzinfo=MONTEVIDEO),
            tz=MONTEVIDEO,
        )

        # An animal present for the whole UTC day of the 5th misses the last
        # three hours of the farm's day.
        assert overlap_days(_day(5), _day(6), local_day) == Decimal("0.875")
