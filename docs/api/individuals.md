# individuals

_Auto-generated. Do not edit by hand._

## GET /api/v1/farms/{farm_id}/assets/{asset_id}/individuals

_List individuals under an asset_

**Responses:**
- `200` → Page_IndividualRead_ — Successful Response
- `422` → HTTPValidationError — Validation Error

## POST /api/v1/farms/{farm_id}/assets/{asset_id}/individuals

_Create an individual under an asset_

Asset must be in `individual` mode. Parents (if any) must belong to the same farm.

**Request body:**
- `tag` (string, required)
- `name` (string | null, optional)
- `birth_date` (string (date) | null, optional)
- `mother_id` (integer | null, optional)
- `father_id` (integer | null, optional)
- `extra` (object, optional)

**Responses:**
- `201` → IndividualRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/assets/{asset_id}/individuals/{individual_id}

_Get one individual_

**Responses:**
- `200` → IndividualRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## PATCH /api/v1/farms/{farm_id}/assets/{asset_id}/individuals/{individual_id}

_Update an individual_

**Request body:**
- `name` (string | null, optional)
- `tag` (string | null, optional)
- `birth_date` (string (date) | null, optional)
- `mother_id` (integer | null, optional)
- `father_id` (integer | null, optional)
- `status` ('active' | 'sold' | 'deceased' | 'archived' | null, optional)
- `extra` (object | null, optional)

**Responses:**
- `200` → IndividualRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## DELETE /api/v1/farms/{farm_id}/assets/{asset_id}/individuals/{individual_id}

_Delete an individual_

**Responses:**
- `204` → any — Successful Response
- `422` → HTTPValidationError — Validation Error

## Types

### HTTPValidationError

- `detail` (ValidationError[], optional)

### IndividualCreate

- `tag` (string, required)
- `name` (string | null, optional)
- `birth_date` (string (date) | null, optional)
- `mother_id` (integer | null, optional)
- `father_id` (integer | null, optional)
- `extra` (object, optional)

### IndividualRead

- `id` (integer, required)
- `farm_id` (integer, required)
- `asset_id` (integer, required)
- `name` (string | null, required)
- `tag` (string, required)
- `birth_date` (string (date) | null, required)
- `mother_id` (integer | null, required)
- `father_id` (integer | null, required)
- `status` ('active' | 'sold' | 'deceased' | 'archived', required)
- `extra` (object, required)
- `created_at` (string (date-time), required)
- `updated_at` (string (date-time), required)

### IndividualUpdate

- `name` (string | null, optional)
- `tag` (string | null, optional)
- `birth_date` (string (date) | null, optional)
- `mother_id` (integer | null, optional)
- `father_id` (integer | null, optional)
- `status` ('active' | 'sold' | 'deceased' | 'archived' | null, optional)
- `extra` (object | null, optional)

### PageMeta

- `page` (integer, required)
- `page_size` (integer, required)
- `total` (integer, required)
- `has_next` (boolean, required)

### Page_IndividualRead_

- `data` (IndividualRead[], required)
- `meta` (PageMeta, required)

### ValidationError

- `loc` (string | integer[], required)
- `msg` (string, required)
- `type` (string, required)
- `input` (any, optional)
- `ctx` (object, optional)

### IndividualStatus

**Values:** `active` | `sold` | `deceased` | `archived`

