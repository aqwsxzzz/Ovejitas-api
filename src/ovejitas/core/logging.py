import logging

from rich.console import Console
from rich.logging import RichHandler

console = Console()


def configure_logging(debug: bool = False) -> None:
    """Replace default handlers with a single RichHandler across common loggers."""
    level = logging.DEBUG if debug else logging.INFO
    handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_suppress=["fastapi", "starlette"],
    )
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine"):
        lg = logging.getLogger(name)
        lg.handlers = [handler]
        lg.propagate = False

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
