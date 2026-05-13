import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from starlette.responses import Response

logger = logging.getLogger("ovejitas.request")


def _status_color(status_code: int) -> str:
    if status_code >= 500:
        return "bold red"
    if status_code >= 400:
        return "yellow"
    if status_code >= 300:
        return "cyan"
    return "green"


def _method_color(method: str) -> str:
    return {
        "GET": "cyan",
        "POST": "green",
        "PUT": "yellow",
        "PATCH": "yellow",
        "DELETE": "red",
    }.get(method, "white")


def register_request_logging(app: FastAPI) -> None:
    @app.middleware("http")
    async def log_requests(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        method = request.method
        path = request.url.path
        status_code = response.status_code
        msg = (
            f"[{_method_color(method)}]{method:<6}[/] "
            f"[{_status_color(status_code)}]{status_code}[/] "
            f"[dim]{duration_ms:6.1f}ms[/dim]  {path}"
        )
        if status_code >= 500:
            logger.error(msg, extra={"markup": True})
        elif status_code >= 400:
            logger.warning(msg, extra={"markup": True})
        else:
            logger.info(msg, extra={"markup": True})
        return response
