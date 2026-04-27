# reports

_Auto-generated. Do not edit by hand._

## GET /api/v1/farms/{farm_id}/reports/profitability

_R1 — income minus expense per asset_

One row per (asset, currency). Events with NULL amount/currency are excluded. Different currencies are never silently summed.

**Responses:**
- `200` → ProfitabilityReport — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/reports/production

_R2 — SUM(quantity) bucketed over time_

Default type=production. Pass type=observation + unit=unit to get headcount deltas. Grouped by (bucket, asset_id, unit, category_id).

**Responses:**
- `200` → ProductionReport — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/reports/cost-per-unit

_R3 — expense total ÷ produced quantity, per asset_

Requires `unit` (what counts as one produced unit). One row per (asset, currency). Assets without BOTH production (in the given unit) and expense events are omitted — a currency cannot be inferred without an expense row. The expense total is not unit-filtered: all of the asset's expenses are attributed to the queried production unit, so this number is only meaningful for single-output assets.

**Responses:**
- `200` → CostPerUnitReport — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/reports/individuals/{individual_id}/timeline

_R4 — paginated event timeline for one individual_

**Responses:**
- `200` → Page_EventRead_ — Successful Response
- `422` → HTTPValidationError — Validation Error

## Types

### CostPerUnitReport

- `data` (CostPerUnitRow[], required)
- `unit` (string, required)

### CostPerUnitRow

- `asset_id` (integer, required)
- `asset_name` (string, required)
- `currency` (string, required)
- `quantity` (string, required)
- `expense_total` (string, required)
- `cost_per_unit` (string, required)

### EventRead

- `id` (integer, required)
- `farm_id` (integer, required)
- `asset_id` (integer, required)
- `individual_id` (integer | null, required)
- `type` ('production' | 'expense' | 'income' | 'observation' | 'reproductive' | 'acquisition' | 'mortality', required)
- `category_id` (integer | null, required)
- `occurred_at` (string (date-time), required)
- `quantity` (string | null, required)
- `unit` (string | null, required)
- `amount` (string | null, required)
- `currency` (string | null, required)
- `notes` (string | null, required)
- `payload` (object, required)
- `idempotency_key` (string | null, required)
- `created_by` (integer, required)
- `created_at` (string (date-time), required)
- `updated_at` (string (date-time), required)

### HTTPValidationError

- `detail` (ValidationError[], optional)

### PageMeta

- `page` (integer, required)
- `page_size` (integer, required)
- `total` (integer, required)
- `has_next` (boolean, required)

### Page_EventRead_

- `data` (EventRead[], required)
- `meta` (PageMeta, required)

### ProductionReport

- `data` (ProductionRow[], required)
- `bucket` ('day' | 'week' | 'month', required)
- `type` ('production' | 'expense' | 'income' | 'observation' | 'reproductive' | 'acquisition' | 'mortality', required)

### ProductionRow

- `bucket_start` (string (date-time), required)
- `asset_id` (integer, required)
- `unit` (string, required)
- `category_id` (integer | null, required)
- `total` (string, required)

### ProfitabilityReport

- `data` (ProfitabilityRow[], required)

### ProfitabilityRow

- `asset_id` (integer, required)
- `asset_name` (string, required)
- `currency` (string, required)
- `income_total` (string, required)
- `expense_total` (string, required)
- `net` (string, required)

### ValidationError

- `loc` (string | integer[], required)
- `msg` (string, required)
- `type` (string, required)
- `input` (any, optional)
- `ctx` (object, optional)

### Bucket

**Values:** `day` | `week` | `month`

### EventType

**Values:** `production` | `expense` | `income` | `observation` | `reproductive` | `acquisition` | `mortality`

