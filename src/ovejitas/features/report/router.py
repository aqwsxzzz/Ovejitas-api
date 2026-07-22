"""Aggregator for the report routes. Every report lives in a routes_* module
grouped by report family; this file only mounts them under the shared
farm-scoped prefix so the mounted paths stay in one place."""

from fastapi import APIRouter

from ovejitas.features.report import (
    routes_aggregate,
    routes_individual,
    routes_inventory,
    routes_produce,
    routes_production,
    routes_profitability,
)

router = APIRouter(prefix="/farms/{farm_id}/reports", tags=["reports"])

router.include_router(routes_profitability.router)
router.include_router(routes_aggregate.router)
router.include_router(routes_production.router)
router.include_router(routes_produce.router)
router.include_router(routes_inventory.router)
router.include_router(routes_individual.router)
