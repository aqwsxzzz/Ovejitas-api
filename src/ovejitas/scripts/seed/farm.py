"""Demo owner + farm. The only rows the seed builds directly — there is no
action behind creating a user or a farm."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.security import hash_password
from ovejitas.features.currency.models import Currency
from ovejitas.features.farm.models import Farm
from ovejitas.features.farm_member.models import FarmMember, FarmRole
from ovejitas.features.user.models import User

DEMO_EMAIL = "demo@ovejitas.app"
DEMO_PASSWORD = "Password1"


async def already_seeded(db: AsyncSession) -> bool:
    stmt = select(User.id).where(User.email == DEMO_EMAIL)
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def seed_user_and_farm(db: AsyncSession) -> tuple[User, Farm]:
    user = User(email=DEMO_EMAIL, name="Demo", password_hash=hash_password(DEMO_PASSWORD))
    farm = Farm(name="Granja Demo", default_currency="USD")
    db.add_all([user, farm])
    await db.flush()
    db.add(Currency(farm_id=farm.id, code="USD", name="US Dollar"))
    db.add(FarmMember(user_id=user.id, farm_id=farm.id, role=FarmRole.OWNER))
    await db.commit()
    return user, farm
