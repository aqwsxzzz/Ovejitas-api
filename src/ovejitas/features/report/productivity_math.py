"""Pure math for the production-productivity report: within-family unit
conversion and resolving a query's bounds onto the farm's calendar.

Kept separate from the report orchestration so the fiddly bits are small and
independently testable. Headcount lives in ``headcount.py`` — it needs the
database, and "how many animals were here" is its own question.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from ovejitas.features.event.types import Unit

YEAR_DAYS = Decimal(365)

# Size of one unit in its family's base unit (count=unit, volume=ml, mass=g).
# Same-family membership is guaranteed for stored production events by the
# event guard, so conversion is always within one of these scales.
_BASE_SIZE: dict[Unit, Decimal] = {
    Unit.UNIT: Decimal(1),
    Unit.DOZEN: Decimal(12),
    Unit.ML: Decimal(1),
    Unit.L: Decimal(1000),
    Unit.GAL: Decimal("3785.411784"),
    Unit.G: Decimal(1),
    Unit.KG: Decimal(1000),
    Unit.LB: Decimal("453.59237"),
    Unit.T: Decimal(1_000_000),
}


def convert(quantity: Decimal, from_unit: Unit, to_unit: Unit) -> Decimal:
    """Convert a quantity between two units of the same measurement family."""
    if from_unit == to_unit:
        return quantity
    return quantity * _BASE_SIZE[from_unit] / _BASE_SIZE[to_unit]


@dataclass(frozen=True)
class Window:
    """A productivity window resolved onto the farm's calendar.

    A whole number of calendar days: ``start`` is the midnight opening
    ``date_from``'s day, ``end`` the exclusive midnight closing ``date_to``'s.
    Both the produced numerator and the animal-day denominator are bounded by
    these same two instants, so the two halves of the ratio can never disagree
    about which days they cover.
    """

    start: datetime
    end: datetime
    tz: ZoneInfo

    @property
    def first_day(self) -> date:
        """First farm-local calendar day the window touches."""
        return self.start.astimezone(self.tz).date()

    @property
    def last_day(self) -> date:
        """Last farm-local calendar day the window touches (``end`` is exclusive)."""
        return (self.end - timedelta(microseconds=1)).astimezone(self.tz).date()

    def local_midnight(self, day: date) -> datetime:
        """The instant calendar day ``day`` opens on the farm.

        Effective-dated target rows store bare calendar dates — a farmer saying
        "this rate applies from the 10th" means the 10th where the animals are.
        Reading one as UTC midnight starts the rate three hours early at UTC-3,
        which silently mis-weights every animal-day in the first segment.
        """
        return datetime(day.year, day.month, day.day, tzinfo=self.tz)


def resolve_window(date_from: datetime, date_to: datetime, tz: ZoneInfo) -> Window:
    """Widen the bounds to the whole calendar days they fall on.

    The report is day-grained — a target is a per-day (or per-year) rate — so
    both ends snap to day boundaries. Asking about today at 18:45 must expect a
    whole day's goal: with the lower bound left raw, a 500-head flock at 1/head
    expects 109 rather than 500, because only 5¼ hours of the day remain to
    integrate over. The same reasoning closes the upper bound at the *end* of
    ``date_to``'s day, so an in-progress day is never prorated to elapsed hours.

    Both ends snap in the bound's own frame, matching ``apply_date_range``:
    after localization a naive bound already carries the farm's zone, and an
    explicit offset is the client naming a frame deliberately. ``tz`` is carried
    separately because target rows store bare dates that have no frame of their
    own — see ``local_midnight``.
    """
    start = datetime.combine(date_from.date(), time(), tzinfo=date_from.tzinfo)
    last_day_start = datetime.combine(date_to.date(), time(), tzinfo=date_to.tzinfo)
    return Window(start=start, end=last_day_start + timedelta(days=1), tz=tz)
