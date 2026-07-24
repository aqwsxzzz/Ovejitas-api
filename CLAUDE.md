# CLAUDE.md

```yaml
project:
  name: ovejitas-api
  type: REST API
  domain: livestock / farm management (generic event-sourced model)
  language: python 3.12+
  framework: fastapi
  orm: sqlalchemy 2.0 async
  migrations: alembic
  validation: pydantic v2
  package_manager: uv
  database: postgresql 16
  entry: src/ovejitas/main.py
  src_dir: src/
  status: rebuild complete; active development on develop. Core = asset/individual/event/event_category. See docs/domain-model.md and src/ovejitas/features/*/models.py for the current schema; docs/domain-rebuild-plan.md is historical

scripts:
  dev: uv run uvicorn ovejitas.main:app --reload --host 0.0.0.0
  start: uv run uvicorn ovejitas.main:app --host 0.0.0.0
  test: uv run pytest
  lint: uv run ruff check
  format: uv run ruff format
  typecheck: uv run mypy src
  migrate: uv run alembic upgrade head
  migrate_new: uv run alembic revision --autogenerate -m "<msg>"
  migrate_down: uv run alembic downgrade -1
  seed: uv run python -m ovejitas.scripts.seed

formatting:
  tool: ruff (format + check)
  line_length: 100
  quotes: double
  indent: 4 spaces
  import_sort: ruff (isort-compatible)

naming:
  files: snake_case
  modules: snake_case
  variables: snake_case
  functions: snake_case
  classes: PascalCase
  constants: UPPER_SNAKE_CASE
  db_columns: snake_case
  db_tables: snake_case (singular, e.g. asset)

python:
  target: 3.12+
  type_hints: required on all function signatures
  strict: mypy --strict (no implicit Any, no untyped defs)
  async: default for I/O; sync only for pure helpers
  no_star_imports: true

architecture:
  pattern: feature-folders (everything per-feature close together)
  api_prefix: /api/v1
  app_factory: src/ovejitas/main.py

project_layout:
  root: src/ovejitas/
  core:
    location: src/ovejitas/core/
    files:
      - config.py        # pydantic-settings, env vars
      - db.py            # async engine, session, get_db dep
      - security.py      # JWT encode/decode, password hashing
      - deps.py          # get_current_user, require_farm_member, pagination
      - errors.py        # domain exceptions + FastAPI exception handlers
      - pagination.py    # Page, PageParams, paginate()
      - filters.py       # FilterParams base, apply_filters()
      - search.py        # search helper (ILIKE over configured columns)
  features:
    location: src/ovejitas/features/{name}/
    files:
      - router.py        # APIRouter, thin — validation + dep injection
      - models.py        # SQLAlchemy models
      - schemas.py       # Pydantic request/response schemas
      - service.py       # business logic, only layer touching DB
      - deps.py          # feature-local dependencies (optional)
      - guards.py        # cross-entity assertions (optional, e.g. event)
  rules:
    - singular feature name (asset, event, not events)
    - service is only layer touching the database
    - routers never import models directly — go through service
    - schemas.py owns serialization; service returns models, router returns schemas
    - cross-feature calls go service → service, never model imports

core_domain:
  primitives: asset, individual, event_category, event
  event_types: [production, expense, income, observation, reproductive, acquisition, mortality, inventory]
  validation: pydantic discriminated union on event.type (acquisition/mortality are system-only, not in EventCreate)
  details: see docs/domain-model.md and docs/events-and-actions.md

list_endpoints:
  mandatory_from_day_0: true
  every_list_endpoint_supports:
    - pagination: offset/limit + total count, standard response envelope
    - search: q param, ILIKE over feature-declared searchable columns
    - filtering: typed query params per feature, declared in schemas.py
    - sorting: sort param, whitelist of allowed columns per feature
  response_envelope:
    data: list[Schema]
    meta:
      page: int
      page_size: int
      total: int
      has_next: bool
  implementation:
    - core/pagination.py owns PageParams (page, page_size) + Page[T] generic
    - core/filters.py owns FilterParams base (date_from, date_to, etc.) per feature extends
    - core/search.py owns search(query, columns, term) helper
    - service accepts (params, filters, search_term, sort) — returns (rows, total)
    - router wraps into Page[Schema] response model
  list_endpoint_shape: |
    async def list_items(
        params: PageParams = Depends(),
        filters: ItemFilters = Depends(),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> Page[ItemRead]: ...

schemas:
  library: pydantic v2
  patterns:
    - {Name}Create — POST body
    - {Name}Update — PATCH body (all fields optional)
    - {Name}Read — response model (exposes fields, hides secrets)
    - {Name}Filters — list query params (extends FilterParams)
  config:
    from_attributes: true (model → schema conversion)
    extra: forbid (reject unknown fields on input)
    discriminator: used on event type union

responses:
  success: return Pydantic schema directly; FastAPI serializes
  error: raise domain exception (AppError subclass); handler formats envelope
  envelope:
    success: { data, meta? }
    error: { detail, code, errors[]? }

auth:
  method: JWT bearer tokens
  header: Authorization: Bearer <token>
  access_token_ttl: 15m
  refresh_token_ttl: 7d
  password_hash: passlib[bcrypt]
  dep: get_current_user (required), get_current_user_optional (public)
  farm_scope: require_farm_member(farm_id) dep — checks membership on every farm-scoped route

database:
  engine: asyncpg via sqlalchemy.ext.asyncio
  session: scoped per request via FastAPI dep
  migrations:
    tool: alembic
    location: migrations/versions/
    naming: alembic auto-timestamp + slug
    must_have: up and down functions
  pool:
    size: 5
    max_overflow: 10
    pool_pre_ping: true
  query_rules:
    - no raw SQL unless justified (use select(), insert(), update())
    - prefer select() with explicit columns; avoid model.query loading everything
    - eager-load relationships with selectinload / joinedload — never lazy in async
    - use SAVEPOINT for nested transactions
  errors:
    - catch IntegrityError in service, re-raise as ConflictError
    - catch NoResultFound in service, re-raise as NotFoundError

logging:
  use: logging.getLogger(__name__) + structlog optional
  never: print()

deployment:
  containerization: docker multi-stage
  compose: postgres + app with hot-reload volumes
  env_file: .env (see .env.example)

cors:
  origins: ALLOWED_ORIGINS env var, comma separated
  credentials: true
  methods: [GET, POST, PUT, PATCH, DELETE, OPTIONS]

docs:
  prd: docs/prd_granjas.md
  rebuild_plan: docs/domain-rebuild-plan.md
  api_testing: little-sheep/ (Bruno collection — rewrite pending)

test_framework: pytest + pytest-asyncio + httpx.AsyncClient
test_factories: polyfactory
test_rules:
  - integration tests use real postgres (testcontainers or compose service)
  - no mocking the DB — mock only external HTTP
  - Arrange-Act-Assert structure
  - one assertion per concept

docker:
  rule: ALWAYS run commands inside Docker containers, never on host
  app_container: app
  dev: docker compose up
  exec_pattern: docker compose exec app <command>
  examples:
    - docker compose exec app uv run pytest
    - docker compose exec app uv run alembic upgrade head
    - docker compose exec app uv run alembic revision --autogenerate -m "msg"

<!-- claude-skills:skill-evaluation:start -->
## Skills

BEFORE writing ANY code, you MUST:

1. List EVERY skill available: check `.claude/skills/` (project) and `~/.claude/skills/` (global). The system-reminder's available-skills section is a hint, not the source of truth — if it's missing or empty, still check the directories.
2. For each skill, write: [skill-name] → ACTIVATE / SKIP — [one-line reason]
3. Call Skill(name) for every skill marked ACTIVATE
4. Emit the literal token `[skills-checked]` on its own line
5. Only THEN proceed to implementation

A PreToolUse gate hook blocks Write/Edit/MultiEdit until the `[skills-checked]` token appears in your response since the most recent user prompt. The gate fires once per turn — the first blocked edit is the signal to evaluate skills, then retry. If you skip the evaluation, your response is INCOMPLETE and WRONG.
<!-- claude-skills:skill-evaluation:end -->

```

<!-- claude-skills:file-size:start -->
## File Size Enforcement

- **Never write a file longer than 200 lines of code.** If a file would exceed 200 lines, split it into smaller modules before writing.
- This rule applies during skill evaluation: if the code you're about to write would exceed 200 lines in any single file, refactor into multiple files first.
- Skill evaluation must check this limit as part of every ACTIVATE decision.
<!-- claude-skills:file-size:end -->
