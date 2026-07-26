"""Anchoring of naive date bounds to a farm's timezone (core.filters)."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select

from ovejitas.core.filters import FilterParams, apply_date_range
from ovejitas.features.event.models import Event

MONTEVIDEO = ZoneInfo("America/Montevideo")  # UTC-3 year-round, no DST ambiguity


class TestLocalized:
    @pytest.mark.parametrize(
        "sent, expected",
        [
            (datetime(2026, 4, 10), datetime(2026, 4, 10, tzinfo=MONTEVIDEO)),
            (datetime(2026, 4, 10, 14, 30), datetime(2026, 4, 10, 14, 30, tzinfo=MONTEVIDEO)),
        ],
        ids=["naive midnight", "naive with time"],
    )
    def test_localized_naive_bound_reads_as_farm_wall_clock(
        self, sent: datetime, expected: datetime
    ) -> None:
        filters = FilterParams(date_from=sent, date_to=sent)

        localized = filters.localized(MONTEVIDEO)

        assert localized.date_from == expected
        assert localized.date_to == expected

    def test_localized_naive_midnight_resolves_three_hours_behind_utc(self) -> None:
        filters = FilterParams(date_to=datetime(2026, 4, 10))

        localized = filters.localized(MONTEVIDEO)

        assert localized.date_to is not None
        assert localized.date_to.astimezone(UTC) == datetime(2026, 4, 10, 3, tzinfo=UTC)

    def test_localized_aware_bound_is_preserved_as_sent(self) -> None:
        sent = datetime(2026, 4, 10, tzinfo=UTC)
        filters = FilterParams(date_from=sent, date_to=sent)

        localized = filters.localized(MONTEVIDEO)

        assert localized.date_from == sent
        assert localized.date_to == sent

    def test_localized_absent_bounds_stay_none(self) -> None:
        localized = FilterParams().localized(MONTEVIDEO)

        assert localized.date_from is None
        assert localized.date_to is None

    def test_localized_leaves_the_original_untouched(self) -> None:
        filters = FilterParams(date_to=datetime(2026, 4, 10))

        filters.localized(MONTEVIDEO)

        assert filters.date_to == datetime(2026, 4, 10)
        assert filters.date_to is not None
        assert filters.date_to.tzinfo is None


class TestApplyDateRangeRejectsNaive:
    @pytest.mark.parametrize(
        "date_from, date_to",
        [
            (datetime(2026, 4, 10), None),
            (None, datetime(2026, 4, 10)),
        ],
        ids=["naive date_from", "naive date_to"],
    )
    def test_apply_date_range_with_naive_bound_raises(
        self, date_from: datetime | None, date_to: datetime | None
    ) -> None:
        with pytest.raises(ValueError, match="must be timezone-aware"):
            apply_date_range(select(Event), Event.occurred_at, date_from, date_to)

    def test_apply_date_range_with_aware_bounds_is_accepted(self) -> None:
        stmt = apply_date_range(
            select(Event),
            Event.occurred_at,
            datetime(2026, 4, 1, tzinfo=MONTEVIDEO),
            datetime(2026, 4, 10, tzinfo=MONTEVIDEO),
        )

        assert stmt.whereclause is not None
