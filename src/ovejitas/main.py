from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from ovejitas.core.config import get_settings
from ovejitas.core.errors import register_error_handlers
from ovejitas.core.logging import configure_logging
from ovejitas.core.middleware import register_request_logging
from ovejitas.core.startup import lifespan
from ovejitas.features.asset.router import router as asset_router
from ovejitas.features.auth.router import router as auth_router
from ovejitas.features.event.router import router as event_router
from ovejitas.features.event_category.router import router as event_category_router
from ovejitas.features.farm.router import router as farm_router
from ovejitas.features.farm_invitation.router import router as farm_invitation_router
from ovejitas.features.flock.router import router as flock_router
from ovejitas.features.harvest.router import router as harvest_router
from ovejitas.features.individual.router import router as individual_router
from ovejitas.features.material_consumption.router import router as material_consumption_router
from ovejitas.features.material_purchase.router import router as material_purchase_router
from ovejitas.features.material_sale.router import router as material_sale_router
from ovejitas.features.report.router import router as report_router

API_PREFIX = "/api/v1"


def _operation_id(route: APIRoute) -> str:
    """Produce `{tag}_{name}` operation IDs so generated clients get clean method names."""
    tag = str(route.tags[0] if route.tags else "default").replace(" ", "_")
    return f"{tag}_{route.name}"


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(debug=settings.debug)
    is_prod = settings.app_env == "production"
    app = FastAPI(
        title="Ovejitas API",
        version="0.1.0",
        debug=settings.debug,
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
        generate_unique_id_function=_operation_id,
        lifespan=lifespan,
    )

    register_error_handlers(app)
    register_request_logging(app)

    if settings.cors_origins_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins_list,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )

    app.include_router(auth_router, prefix=API_PREFIX)
    app.include_router(farm_router, prefix=API_PREFIX)
    app.include_router(farm_invitation_router, prefix=API_PREFIX)
    app.include_router(asset_router, prefix=API_PREFIX)
    app.include_router(individual_router, prefix=API_PREFIX)
    app.include_router(event_category_router, prefix=API_PREFIX)
    app.include_router(event_router, prefix=API_PREFIX)
    app.include_router(material_consumption_router, prefix=API_PREFIX)
    app.include_router(material_purchase_router, prefix=API_PREFIX)
    app.include_router(flock_router, prefix=API_PREFIX)
    app.include_router(harvest_router, prefix=API_PREFIX)
    app.include_router(material_sale_router, prefix=API_PREFIX)
    app.include_router(report_router, prefix=API_PREFIX)

    @app.get("/health", tags=["health"], summary="Liveness check")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
