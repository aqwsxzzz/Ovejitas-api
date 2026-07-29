"""Farm-scoped request dependencies: the farm's timezone, and the query-model
wrapper that anchors date filters to it."""

from collections.abc import Callable, Coroutine
from typing import Annotated, Any
from zoneinfo import ZoneInfo

from fastapi import Depends

from ovejitas.core.deps import DBSession
from ovejitas.core.filters import FilterParams
from ovejitas.features.farm.timezone import farm_timezone
from ovejitas.features.farm_member.deps import FarmMembership


async def get_farm_timezone(membership: FarmMembership, db: DBSession) -> ZoneInfo:
    """Resolve the timezone of the farm this request is scoped to.

    Hangs off the membership rather than the raw path param so the caller is
    proven to belong to the farm before any of its rows are read.
    """
    return await farm_timezone(db, membership.farm_id)


FarmTimezone = Annotated[ZoneInfo, Depends(get_farm_timezone)]


def farm_local[F: FilterParams](model: type[F]) -> Callable[..., Coroutine[Any, Any, F]]:
    """Inject ``model`` as query params, with naive date bounds read as farm-local.

    Use in place of a bare ``Depends()`` on any filter or report-query model.
    Without it a client's ``date_from=2026-07-26`` reaches the query as UTC
    midnight — the previous evening on any farm west of Greenwich — so a
    whole-day window silently covers the wrong day and reports drop the last
    hours of the farmer's day.

    The dependency is built here rather than declared inline because the model
    type is only known at call time; FastAPI resolves ``Depends(model)`` the
    same way ``Annotated[model, Depends()]`` would.
    """

    async def dependency(
        filters: F = Depends(model),
        tz: ZoneInfo = Depends(get_farm_timezone),
    ) -> F:
        return filters.localized(tz)

    return dependency
