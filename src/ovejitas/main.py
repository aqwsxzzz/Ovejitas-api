from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from ovejitas.core.config import get_settings
from ovejitas.core.errors import register_error_handlers
from ovejitas.features.auth.router import router as auth_router

API_PREFIX = "/api/v1"


def _operation_id(route: APIRoute) -> str:
    """Produce `{tag}_{name}` operation IDs so generated clients get clean method names."""
    tag = (route.tags[0] if route.tags else "default").replace(" ", "_")
    return f"{tag}_{route.name}"


def create_app() -> FastAPI:
    settings = get_settings()
    is_prod = settings.app_env == "production"
    app = FastAPI(
        title="Ovejitas API",
        version="0.1.0",
        debug=settings.debug,
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
        generate_unique_id_function=_operation_id,
    )

    register_error_handlers(app)

    if settings.cors_origins_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins_list,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )

    app.include_router(auth_router, prefix=API_PREFIX)

    @app.get("/health", tags=["health"], summary="Liveness check")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
