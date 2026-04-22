# Domain Rebuild Plan

Rebuild the backend around three primitives — **Production Unit**, **Individual**, **Event** — replacing the current tree of ~24 domain-specific resources. Also a full stack swap: **Node/Fastify/Sequelize → Python/FastAPI/SQLAlchemy**. Goal: a small, generic, scalable system that supports gallinas and vacas today and crops, beehives, aquaculture tomorrow without backend changes.

Reference: [PRD v1 simplificado](./prd_granjas.md) · Inspired by the [farmOS Asset + Log model](https://farmos.org/model/).

## Stack

| concern | choice |
|---|---|
| Language | Python 3.12+ |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 async |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Package manager | uv |
| Auth | JWT bearer tokens (Authorization header) |
| Testing | pytest + pytest-asyncio + httpx.AsyncClient + polyfactory |
| DB | PostgreSQL 16 |
| Container | Docker multi-stage + compose with hot-reload volumes |
| Layout | `src/` + feature folders |
| Branch | `feat/domain-rebuild` off `develop` (in-repo rewrite) |

## Principles

- Three primitives, no per-domain tables.
- System defines **event types** (closed enum). User defines **categories** (open, per-farm).
- Typed columns for anything filtered, aggregated, or constrained. JSONB only for the tail.
- Reports drive schema. Every core report is one indexed aggregate.
- Router is thin (validation + dep injection). Service is the only layer touching the DB.

## Project Layout

```
src/ovejitas/
  core/
    config.py         # pydantic-settings
    db.py             # async engine, session dep
    security.py       # JWT, password hashing
    deps.py           # get_db, get_current_user, require_farm_member
    errors.py         # domain exceptions + handlers
    pagination.py     # shared list params
  features/
    auth/
      router.py models.py schemas.py service.py
    farm/
      router.py models.py schemas.py service.py deps.py
    farm_member/      # invitations + membership
    production_unit/
      router.py models.py schemas.py service.py
    individual/
    event_category/
    event/
      router.py models.py schemas.py service.py guards.py
    report/
      router.py service.py schemas.py
  main.py             # app factory, router mounts, middleware
migrations/           # alembic
tests/
  unit/
  integration/
  factories/          # polyfactory
pyproject.toml
uv.lock
```

Feature folders are self-contained: models, schemas, router, service together. Cross-feature usage goes via `service` objects, never by importing another feature's model into a router.

## What Stays / What Goes

Everything is rewritten — no code reuse from the Node tree.

Test data is disposable. New branch wipes the database and builds schema fresh via Alembic.

## Schema

### `production_unit`
Container for activity. Flexible, user-named.

| column | type | notes |
|---|---|---|
| id | bigint identity | PK |
| farm_id | bigint | FK |
| name | text | "Gallinas", "Vacas lecheras" |
| mode | enum | `aggregated` \| `individual` |
| location | text? | free text, e.g. "Galpón norte" |
| description | text? | |
| created_at / updated_at | timestamptz | |

Index: `(farm_id)`.

### `individual`
Optional. Only created when unit is `individual` mode.

| column | type | notes |
|---|---|---|
| id | bigint identity | PK |
| farm_id | bigint | FK (denormalized for scoping) |
| production_unit_id | bigint | FK |
| name | text | "Vaca A" |
| tag | text? | ear tag, external id |
| birth_date | date? | |
| mother_id | bigint? | FK → individual |
| father_id | bigint? | FK → individual |
| status | enum | `active` \| `sold` \| `deceased` \| `archived` |
| metadata | jsonb | breed, color, free-form |
| created_at / updated_at | timestamptz | |

Indexes: `(production_unit_id)`, `(farm_id, status)`.

### `event_category`
User-defined labels per farm, scoped by event type.

| column | type | notes |
|---|---|---|
| id | bigint identity | PK |
| farm_id | bigint | FK |
| type | enum | matches `event.type` |
| name | text | "huevos", "alimento balanceado" |
| color | text? | UI hint |
| archived_at | timestamptz? | soft-hide from pickers |

Unique: `(farm_id, type, name)`.

### `event`
Core engine. Single table, discriminated by `type`.

| column | type | notes |
|---|---|---|
| id | bigint identity | PK |
| farm_id | bigint | FK |
| production_unit_id | bigint | FK |
| individual_id | bigint? | FK |
| type | enum | `production` \| `expense` \| `income` \| `observation` \| `reproductive` |
| category_id | bigint? | FK → event_category |
| occurred_at | timestamptz | |
| quantity | numeric? | production / observation |
| unit | text? | 'unit', 'kg', 'L' |
| amount | numeric(14,2)? | expense / income |
| currency | char(3)? | ISO 4217 |
| notes | text? | |
| payload | jsonb | per-type tail (see matrix) |
| idempotency_key | text? | offline retry dedupe |
| created_by | bigint | FK → user |
| created_at / updated_at | timestamptz | |

Indexes:
- `(farm_id, occurred_at DESC)` — dashboards
- `(production_unit_id, type, occurred_at DESC)` — per-unit reports
- `(individual_id, occurred_at DESC) WHERE individual_id IS NOT NULL` — timeline
- `(category_id) WHERE category_id IS NOT NULL`
- `unique (farm_id, idempotency_key) WHERE idempotency_key IS NOT NULL`

DB CHECK: `type <> 'reproductive' OR individual_id IS NOT NULL`.

## Per-Type Field Matrix

| type | quantity | unit | amount | currency | individual_id | payload |
|---|---|---|---|---|---|---|
| production | req | req | — | — | opt | `{}` |
| expense | — | — | req | req | opt | `{ vendor?, invoice_no? }` |
| income | — | — | req | req | opt | `{ buyer?, payment_method? }` |
| observation | opt | opt | — | — | opt | `{ diagnosis?, treatment?, dose? }` |
| reproductive | — | — | — | — | **required** | `{ offspring_count?, outcome? }` |

Enforced via a **Pydantic discriminated union** on `type` (`Field(discriminator='type')`). FastAPI rejects wrong-shape requests before they reach the service.

## List Endpoints — Day-0 Requirements

Every list endpoint (units, individuals, categories, events, reports when listable) ships from day 0 with:

- **Pagination** — `?page=1&page_size=20`. Response envelope carries `page`, `page_size`, `total`, `has_next`.
- **Search** — `?q=<term>`. Per-feature whitelist of searchable text columns (e.g. event.notes, individual.name/tag, production_unit.name). Case-insensitive `ILIKE`.
- **Filtering** — typed query params per feature; common: `date_from`, `date_to`, `farm_id` (implicit from auth), feature-specific: `type`, `category_id`, `production_unit_id`, `individual_id`, `status`.
- **Sorting** — `?sort=-occurred_at,name`. Whitelisted per feature; `-` prefix for DESC.

Implementation lives in `src/ovejitas/core/`:
- `pagination.py` — `PageParams` dep + `Page[T]` generic response.
- `filters.py` — `FilterParams` base; each feature extends in its `schemas.py`.
- `search.py` — `apply_search(stmt, columns, term)` helper.

Service signature pattern:
```python
async def list_items(
    *, filters: ItemFilters, search: str | None, sort: str | None,
    page: PageParams, farm_id: int,
) -> tuple[list[Item], int]: ...
```

Router pattern:
```python
@router.get("", response_model=Page[ItemRead])
async def list_items(
    params: PageParams = Depends(),
    filters: ItemFilters = Depends(),
    search: str | None = Query(None, alias="q"),
    sort: str | None = None,
    svc: ItemService = Depends(),
    farm_id: int = Depends(require_farm_member),
) -> Page[ItemRead]:
    rows, total = await svc.list_items(...)
    return Page.build(rows, total, params)
```

No list endpoint ships without all four. Applies equally to the very first resource built in Phase 2.

## Service-Layer Guards

`EventService.create` / `update` must assert:

1. If `individual_id` set: individual exists, `individual.production_unit_id == input.production_unit_id`.
2. If `individual_id` set: unit's `mode == 'individual'`.
3. If `category_id` set: category exists, `category.farm_id == input.farm_id`, `category.type == input.type`.
4. All referenced entities (`unit`, `individual`, `category`) belong to the same farm as the event.

Single chokepoint; routers never touch models directly.

## Core Reports (drive the schema)

All four resolve to one indexed aggregate — no JSONB extraction.

- **R1 Profitability per unit** — `SUM(CASE WHEN type=...) GROUP BY production_unit_id` over `(farm_id, occurred_at)`.
- **R2 Production over time** — `date_trunc + SUM(quantity) GROUP BY day, category_id, unit`.
- **R3 Cost per produced unit** — CTE of R1 expense side ÷ R2 quantity, per unit.
- **R4 Individual timeline** — `WHERE individual_id=? ORDER BY occurred_at DESC` on partial index.

## Design Decisions

| decision | choice | why |
|---|---|---|
| Auth transport | JWT bearer in `Authorization` header | mobile-friendly, stateless |
| Currency | per-event column + `farm.default_currency` | multi-currency farms possible |
| Event deletion | hard delete | audit log out of scope for v1 |
| Multi-unit events | split into one event per unit | keeps schema clean |
| Category on event | optional | don't block quick entry; UI encourages |
| Species / breed | no tables | free text on unit name or `individual.metadata` |
| Parentesco | `mother_id` / `father_id` on individual | simplest thing that covers PRD |
| Multi-measurement events | deferred | add child `event_measurement` table later if needed |
| JSONB indexing | none in v1 | add expression index per use case if it appears |
| Background jobs | none in v1 | add ARQ/Celery when first real need appears |

## Docker

Multi-stage:
1. **builder** — `uv sync --frozen`, compile wheels.
2. **runtime** — slim base, copy venv + source, non-root user, `uvicorn ovejitas.main:app`.

`docker-compose.yml` for dev:
- `db` — postgres:16-alpine, named volume for data.
- `app` — build target = runtime, bind-mount `./src` for hot reload, command `uvicorn ... --reload`.
- Healthcheck on `/health`.

Run commands inside the `app` container (CLAUDE.md rule unchanged): `docker compose exec app alembic upgrade head`, `docker compose exec app pytest`, etc.

## Phased Execution

Each phase ends with green `uv run pytest` (where applicable) and a commit.

0. **Branch + prep** — `feat/domain-rebuild` off `develop`. Delete Node source tree. Scaffold `pyproject.toml`, `uv.lock`, src layout, Dockerfile, compose, `.env.example`.
1. **Core** — `config`, async DB session, JWT security, `deps`, error handlers, health endpoint, **pagination + filters + search helpers** (so every list endpoint in later phases inherits them).
2. **Auth + Farm** — user registration, login (tokens), farm CRUD, farm_member, invitations.
3. **Domain schema** — Alembic migration for `production_unit`, `individual`, `event_category`, `event`. SQLAlchemy models + relationships.
4. **Domain routes** — Pydantic schemas (incl. discriminated union for events), services, routers behind `require_farm_member` dep.
5. **Reports** — four read-only endpoints under `/api/v1/reports`.
6. **Tests + seed** — pytest suite covering the 5 EventService guard cases, polyfactory factories, seed script for gallinas (aggregated) + vacas (individual, 3 with parentage).
7. **Docs** — rewrite root `CLAUDE.md` for the Python stack, add `docs/domain-model.md` reference.

## Open / Future

- Add `event_measurement` child table if single `quantity` proves insufficient.
- Rename `production_unit` → `asset` if scope expands to land, equipment, plots.
- GIN index on `payload` only if a concrete filter use case appears.
- Migrate old data? **No** — wipe and reseed.
- Mobile client — bearer tokens already make this trivial; generate client from OpenAPI schema.
