"""R4 timeline — the paginated event history of one individual.

Scoped to the farm before anything is read: an individual from another farm is
reported as not found rather than exposing its events.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError
from ovejitas.core.filters import apply_date_range
from ovejitas.core.pagination import PageParams
from ovejitas.features.event.models import Event
from ovejitas.features.individual.models import Individual
from ovejitas.features.report.schemas_individual import TimelineQuery


async def timeline(
    db: AsyncSession,
    farm_id: int,
    individual_id: int,
    q: TimelineQuery,
    page: PageParams,
) -> tuple[list[Event], int]:
    owner = await db.execute(
        select(Individual.id).where(
            Individual.id == individual_id,
            Individual.farm_id == farm_id,
        )
    )
    if owner.scalar_one_or_none() is None:
        raise NotFoundError("Individual not found")

    stmt = select(Event).where(
        Event.farm_id == farm_id,
        Event.individual_id == individual_id,
    )
    stmt = apply_date_range(stmt, Event.occurred_at, q.date_from, q.date_to)
    if q.type is not None:
        stmt = stmt.where(Event.type == q.type)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Event.occurred_at.desc()).offset(page.offset).limit(page.limit)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows), total
