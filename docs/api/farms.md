# farms

_Auto-generated. Do not edit by hand._

## GET /api/v1/farms/{farm_id}

_Get a farm_

**Responses:**
- `200` → FarmRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## PATCH /api/v1/farms/{farm_id}

_Update a farm_

**Request body:**
- `name` (string | null, optional)
- `default_currency` (string | null, optional)

**Responses:**
- `200` → FarmRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## Types

### FarmRead

- `id` (integer, required)
- `name` (string, required)
- `default_currency` (string, required)
- `created_at` (string (date-time), required)
- `updated_at` (string (date-time), required)

### FarmUpdate

- `name` (string | null, optional)
- `default_currency` (string | null, optional)

### HTTPValidationError

- `detail` (ValidationError[], optional)

### ValidationError

- `loc` (string | integer[], required)
- `msg` (string, required)
- `type` (string, required)
- `input` (any, optional)
- `ctx` (object, optional)

