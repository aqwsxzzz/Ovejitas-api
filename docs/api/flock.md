# flock

_Auto-generated. Do not edit by hand._

## POST /api/v1/farms/{farm_id}/assets/{asset_id}/flock/acquisitions

_Record a flock acquisition_

Increments the flock headcount by `quantity` head via an INVENTORY event; when `amount` is given, also books a paired EXPENSE in the farm's default currency. The asset must be `animal` + `aggregated`.

**Request body:**
- `occurred_at` (string (date-time), optional)
- `quantity` (integer, required)
- `amount` (number | string | null, optional)

**Responses:**
- `201` → FlockActionRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## POST /api/v1/farms/{farm_id}/assets/{asset_id}/flock/sales

_Record a flock sale_

Decrements the flock headcount by `quantity` head and books a paired INCOME event for `amount`. Rejected with 409 if it would drive the headcount below zero.

**Request body:**
- `occurred_at` (string (date-time), optional)
- `quantity` (integer, required)
- `amount` (number | string, required)
- `buyer` (string | null, optional)

**Responses:**
- `201` → FlockActionRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## POST /api/v1/farms/{farm_id}/assets/{asset_id}/flock/mortalities

_Record a flock mortality_

Decrements the flock headcount by `quantity` head and emits a paired MORTALITY event. Rejected with 409 if it would drive the headcount below zero.

**Request body:**
- `occurred_at` (string (date-time), optional)
- `quantity` (integer, required)
- `cause` (string | null, optional)

**Responses:**
- `201` → FlockActionRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## Types

### FlockAcquisitionCreate

- `occurred_at` (string (date-time), optional)
- `quantity` (integer, required)
- `amount` (number | string | null, optional)

### FlockActionRead

- `inventory_event_id` (integer, required)
- `paired_event_id` (integer | null, required)
- `headcount` (string, required)

### FlockMortalityCreate

- `occurred_at` (string (date-time), optional)
- `quantity` (integer, required)
- `cause` (string | null, optional)

### FlockSaleCreate

- `occurred_at` (string (date-time), optional)
- `quantity` (integer, required)
- `amount` (number | string, required)
- `buyer` (string | null, optional)

### HTTPValidationError

- `detail` (ValidationError[], optional)

### ValidationError

- `loc` (string | integer[], required)
- `msg` (string, required)
- `type` (string, required)
- `input` (any, optional)
- `ctx` (object, optional)

