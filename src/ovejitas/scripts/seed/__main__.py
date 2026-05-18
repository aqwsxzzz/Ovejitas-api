"""Seed a demo farm that exercises the full action layer — a chicken flock with
harvests and a cattle herd with a birth — so every row looks like the running
app produced it.

Idempotent by owner email: if the demo user exists the script exits untouched.
A partial run is not rolled back (each action commits its own transaction) — on
failure, drop the database and re-seed.

Run: docker compose exec app uv run python -m ovejitas.scripts.seed
"""

import asyncio
import logging
from datetime import UTC, datetime

import ovejitas.models  # noqa: F401  — register every model on Base.metadata
from ovejitas.core.config import get_settings
from ovejitas.core.db import engine, session_factory
from ovejitas.scripts.seed.cattle import seed_cattle
from ovejitas.scripts.seed.farm import DEMO_EMAIL, DEMO_PASSWORD, already_seeded, seed_user_and_farm
from ovejitas.scripts.seed.flock import seed_flock

logger = logging.getLogger("ovejitas.seed")
logging.basicConfig(level=logging.INFO, format="%(message)s")

TODAY = datetime(2026, 5, 15, 12, 0, tzinfo=UTC)


async def seed() -> None:
    env = get_settings().app_env
    if env != "development":
        raise SystemExit(
            f"seed refuses to run with APP_ENV={env!r}. It creates a "
            "known-credential demo account and only runs in development."
        )
    async with session_factory() as db:
        if await already_seeded(db):
            logger.info("Seed already applied (%s exists). Nothing to do.", DEMO_EMAIL)
            return
        user, farm = await seed_user_and_farm(db)
        await seed_flock(db, user, farm, TODAY)
        await seed_cattle(db, user, farm, TODAY)
    await engine.dispose()
    logger.info("Seed complete — login as %s / %s", DEMO_EMAIL, DEMO_PASSWORD)


if __name__ == "__main__":
    asyncio.run(seed())
