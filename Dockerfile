# syntax=docker/dockerfile:1.7

FROM python:3.14-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /usr/local/bin/

FROM base AS builder
WORKDIR /app
COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project

FROM base AS runtime
WORKDIR /app
RUN groupadd --system app && useradd --system --gid app --home /app app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app src ./src
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src"
USER app
EXPOSE 8000
CMD ["uvicorn", "ovejitas.main:app", "--host", "0.0.0.0", "--port", "8000"]
