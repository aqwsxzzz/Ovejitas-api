"""Upcoming-births read-model — individuals whose latest pregnancy check says
pregnant with an expected due date inside the queried window.

Latest-record-wins: only the newest pregnancy row per individual is considered,
so a more recent check that flips an individual to not-pregnant (after birth or
loss) suppresses the alert.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.individual.models import Individual
from ovejitas.features.pregnancy.models import Pregnancy
from ovejitas.features.report.schemas_individual import UpcomingBirthRow


async def upcoming_births(
    db: AsyncSession, farm_id: int, date_from: datetime, date_to: datetime
) -> list[UpcomingBirthRow]:
    latest = (
        select(
            Pregnancy.individual_id,
            Pregnancy.is_pregnant,
            Pregnancy.offspring_count,
            Pregnancy.expected_due_at,
            Individual.tag.label("individual_tag"),
            Individual.asset_id,
        )
        .join(Individual, Individual.id == Pregnancy.individual_id)
        .where(Pregnancy.farm_id == farm_id)
        .order_by(
            Pregnancy.individual_id,
            Pregnancy.occurred_at.desc(),
            Pregnancy.id.desc(),
        )
        .distinct(Pregnancy.individual_id)
        .subquery()
    )
    stmt = (
        select(latest)
        .where(
            latest.c.is_pregnant.is_(True),
            latest.c.expected_due_at >= date_from,
            latest.c.expected_due_at <= date_to,
        )
        .order_by(latest.c.expected_due_at.asc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        UpcomingBirthRow(
            individual_id=row.individual_id,
            individual_tag=row.individual_tag,
            asset_id=row.asset_id,
            expected_due_at=row.expected_due_at,
            offspring_count=row.offspring_count,
            days_until_due=(row.expected_due_at - date_from).days,
        )
        for row in rows
    ]
