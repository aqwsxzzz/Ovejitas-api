from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from rich.panel import Panel
from rich.table import Table

from ovejitas.core.config import Settings, get_settings
from ovejitas.core.db import engine
from ovejitas.core.logging import console

ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"


def _current_rev(sync_conn: Any) -> str | None:
    ctx = MigrationContext.configure(sync_conn)
    return ctx.get_current_revision()


async def _check_migrations() -> tuple[str | None, str | None, list[str]]:
    cfg = Config(str(ALEMBIC_INI))
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()

    async with engine.connect() as conn:
        current = await conn.run_sync(_current_rev)

    pending: list[str] = []
    if current != head and head is not None:
        for rev in script.iterate_revisions(head, current):
            pending.append(rev.revision)
    return current, head, pending


def _print_banner(settings: Settings) -> None:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="cyan", justify="right")
    table.add_column(style="bold white")
    table.add_row("app", "Ovejitas API v0.1.0")
    env_style = "green" if settings.app_env != "production" else "red"
    table.add_row("env", f"[{env_style}]{settings.app_env}[/{env_style}]")
    table.add_row("debug", "on" if settings.debug else "off")
    table.add_row("docs", "/docs" if settings.app_env != "production" else "disabled")
    console.print(Panel(table, title="[bold green]ready[/bold green]", border_style="green"))


def _print_migration_status(current: str | None, head: str | None, pending: list[str]) -> None:
    if not pending:
        msg = f"[green]db at head[/green] ([dim]{head or 'none'}[/dim])"
        console.print(Panel(msg, title="migrations", border_style="green"))
        return

    lines = [
        f"[yellow]current:[/yellow] [dim]{current or 'none'}[/dim]",
        f"[yellow]head:[/yellow]    [bold]{head}[/bold]",
        f"[yellow]pending:[/yellow] [bold red]{len(pending)}[/bold red] revision(s)",
        "",
        *[f"  [red]•[/red] {rev}" for rev in pending],
        "",
        "[bold]run:[/bold] [cyan]docker compose exec app alembic upgrade head[/cyan]",
    ]
    console.print(
        Panel(
            "\n".join(lines),
            title="[bold red]PENDING MIGRATIONS[/bold red]",
            border_style="red",
        )
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    _print_banner(settings)
    try:
        current, head, pending = await _check_migrations()
        _print_migration_status(current, head, pending)
    except Exception as exc:
        console.print(
            Panel(
                f"[red]migration check failed:[/red] {exc}",
                title="migrations",
                border_style="red",
            )
        )
    yield
