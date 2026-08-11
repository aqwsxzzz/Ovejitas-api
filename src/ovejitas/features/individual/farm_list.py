"""The farm-wide individual list — a read model, kept out of the write path.

Individuals are otherwise reachable only under one asset, which is fine until
you need a sire: rams and bulls are commonly kept in their own lot, so the
animal a farmer wants to name as father is exactly the one the per-asset list
cannot offer. The alternative for a client is fetching every animal asset and
then its individuals, which is one request per lot to fill one dropdown.

No writes, no events — this only reads. It reuses the per-asset list's search
and sort declarations so the two stay answerable the same way, and returns the
same rows, which the router serializes with the unchanged ``IndividualRead``.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.filters import apply_date_range
from ovejitas.core.pagination import PageParams
from ovejitas.core.search import apply_search
from ovejitas.core.sorting import apply_sort
from ovejitas.features.individual.models import Individual
from ovejitas.features.individual.schemas import FarmIndividualFilters
from ovejitas.features.individual.service import SEARCH_COLUMNS, SORT_ALLOWED


async def list_farm_individuals(
    db: AsyncSession,
    *,
    farm_id: int,
    filters: FarmIndividualFilters,
    search: str | None,
    sort: str | None,
    page: PageParams,
) -> tuple[list[Individual], int]:
    """Every individual in the farm, whichever lot it sits in.

    Scoped on ``farm_id`` first, so an ``asset_id`` naming another farm's lot
    narrows to nothing rather than reaching across the boundary.
    """
    stmt = select(Individual).where(Individual.farm_id == farm_id)
    if filters.status is not None:
        stmt = stmt.where(Individual.status == filters.status)
    if filters.asset_id is not None:
        stmt = stmt.where(Individual.asset_id == filters.asset_id)
    stmt = apply_date_range(stmt, Individual.created_at, filters.date_from, filters.date_to)
    stmt = apply_search(stmt, search, SEARCH_COLUMNS)
    stmt = apply_sort(stmt, sort, SORT_ALLOWED)
    if sort is None:
        # Tag, then id: a picker reads in tag order, and the id tiebreak keeps
        # paging stable when two lots reuse a tag.
        stmt = stmt.order_by(Individual.tag.asc(), Individual.id.asc())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset(page.offset).limit(page.limit)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows), total
