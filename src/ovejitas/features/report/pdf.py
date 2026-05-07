"""PDF rendering for reports — Jinja2 + WeasyPrint, es-localized output."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from babel.dates import format_date, format_datetime
from babel.numbers import format_decimal
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

_LOCALE = "es"
_TEMPLATES = Path(__file__).parent / "templates"


def _fmt_number(value: Decimal | float | int | None) -> str:
    if value is None:
        return "—"
    return format_decimal(value, format="#,##0.##", locale=_LOCALE)


def _fmt_money(value: Decimal | float | int | None) -> str:
    if value is None:
        return "—"
    return format_decimal(value, format="#,##0.00", locale=_LOCALE)


def _fmt_date(value: datetime | None) -> str:
    if value is None:
        return "—"
    return format_date(value, format="long", locale=_LOCALE)


def _build_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(_TEMPLATES),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["num"] = _fmt_number
    env.filters["money"] = _fmt_money
    env.filters["date"] = _fmt_date
    return env


_env = _build_env()


def render_pdf(
    template: str,
    *,
    farm_name: str,
    title: str,
    generated_by: str,
    date_from: datetime | None,
    date_to: datetime | None,
    context: dict[str, Any],
) -> bytes:
    tpl = _env.get_template(template)
    html = tpl.render(
        farm_name=farm_name,
        title=title,
        generated_by=generated_by,
        generated_at=format_datetime(datetime.now(), format="medium", locale=_LOCALE),
        date_from=_fmt_date(date_from),
        date_to=_fmt_date(date_to),
        **context,
    )
    return HTML(string=html).write_pdf()
