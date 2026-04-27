# events

_Auto-generated. Do not edit by hand._

## GET /api/v1/farms/{farm_id}/assets/{asset_id}/events

_List events for an asset_

**Responses:**
- `200` → Page_EventRead_ — Successful Response
- `422` → HTTPValidationError — Validation Error

## POST /api/v1/farms/{farm_id}/assets/{asset_id}/events

_Create an event_

Body is a discriminated union on `type`. Reproductive events require `kind=animal` + `individual_id`. Individuals require `mode=individual` and must belong to this asset. Categories must match the event type.

**Request body:**

**Responses:**
- `201` → EventRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/assets/{asset_id}/events/{event_id}

_Get one event_

**Responses:**
- `200` → EventRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## PATCH /api/v1/farms/{farm_id}/assets/{asset_id}/events/{event_id}

_Update an event_

`type` is immutable. Guards still apply to `individual_id` / `category_id`.

**Request body:**
- `occurred_at` (string (date-time) | null, optional)
- `individual_id` (integer | null, optional)
- `category_id` (integer | null, optional)
- `quantity` (number | string | null, optional)
- `unit` (string | null, optional)
- `amount` (number | string | null, optional)
- `currency` (string | null, optional)
- `notes` (string | null, optional)
- `payload` (object | null, optional)

**Responses:**
- `200` → EventRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## DELETE /api/v1/farms/{farm_id}/assets/{asset_id}/events/{event_id}

_Delete an event_

**Responses:**
- `204` → any — Successful Response
- `422` → HTTPValidationError — Validation Error

## Types

### EventAcquisitionCreate

- `occurred_at` (string (date-time), required)
- `individual_id` (integer | null, optional)
- `category_id` (integer | null, optional)
- `notes` (string | null, optional)
- `payload` (object, optional)
- `idempotency_key` (string | null, optional)
- `type` (string, required)
- `quantity` (number | string, required)
- `amount` (number | string | null, optional)
- `currency` (string | null, optional)

### EventExpenseCreate

- `occurred_at` (string (date-time), required)
- `individual_id` (integer | null, optional)
- `category_id` (integer | null, optional)
- `notes` (string | null, optional)
- `payload` (object, optional)
- `idempotency_key` (string | null, optional)
- `type` (string, required)
- `amount` (number | string, required)
- `currency` (string, required)

### EventIncomeCreate

- `occurred_at` (string (date-time), required)
- `individual_id` (integer | null, optional)
- `category_id` (integer | null, optional)
- `notes` (string | null, optional)
- `payload` (object, optional)
- `idempotency_key` (string | null, optional)
- `type` (string, required)
- `amount` (number | string, required)
- `currency` (string, required)

### EventMortalityCreate

- `occurred_at` (string (date-time), required)
- `individual_id` (integer | null, optional)
- `category_id` (integer | null, optional)
- `notes` (string | null, optional)
- `payload` (object, optional)
- `idempotency_key` (string | null, optional)
- `type` (string, required)
- `quantity` (number | string, required)

### EventObservationCreate

- `occurred_at` (string (date-time), required)
- `individual_id` (integer | null, optional)
- `category_id` (integer | null, optional)
- `notes` (string | null, optional)
- `payload` (object, optional)
- `idempotency_key` (string | null, optional)
- `type` (string, required)

### EventProductionCreate

- `occurred_at` (string (date-time), required)
- `individual_id` (integer | null, optional)
- `category_id` (integer | null, optional)
- `notes` (string | null, optional)
- `payload` (object, optional)
- `idempotency_key` (string | null, optional)
- `type` (string, required)
- `quantity` (number | string, required)
- `unit` (string, required)

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

### EventReproductiveCreate

- `occurred_at` (string (date-time), required)
- `individual_id` (integer, required)
- `category_id` (integer | null, optional)
- `notes` (string | null, optional)
- `payload` (object, optional)
- `idempotency_key` (string | null, optional)
- `type` (string, required)

### EventUpdate

- `occurred_at` (string (date-time) | null, optional)
- `individual_id` (integer | null, optional)
- `category_id` (integer | null, optional)
- `quantity` (number | string | null, optional)
- `unit` (string | null, optional)
- `amount` (number | string | null, optional)
- `currency` (string | null, optional)
- `notes` (string | null, optional)
- `payload` (object | null, optional)

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

### ValidationError

- `loc` (string | integer[], required)
- `msg` (string, required)
- `type` (string, required)
- `input` (any, optional)
- `ctx` (object, optional)

### EventType

**Values:** `production` | `expense` | `income` | `observation` | `reproductive` | `acquisition` | `mortality`

