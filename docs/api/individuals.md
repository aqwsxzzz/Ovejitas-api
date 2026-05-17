# individuals

_Auto-generated. Do not edit by hand._

## GET /api/v1/farms/{farm_id}/assets/{asset_id}/individuals

_List individuals under an asset_

**Responses:**
- `200` → Page_IndividualRead_ — Successful Response
- `422` → HTTPValidationError — Validation Error

## POST /api/v1/farms/{farm_id}/assets/{asset_id}/individuals

_Create an individual under an asset_

Asset must be in `individual` mode. Parents (if any) must belong to the same farm. Atomically emits an ACQUISITION event; a `purchased` acquisition also books a paired EXPENSE event for `amount` in the farm's default currency.

**Request body:**
- `tag` (string, required)
- `name` (string | null, optional)
- `birth_date` (string (date) | null, optional)
- `mother_id` (integer | null, optional)
- `father_id` (integer | null, optional)
- `extra` (object, optional)
- `acquired_at` (string (date-time), optional)
- `acquisition_method` ('purchased' | 'born' | 'other', optional)
- `amount` (number | string | null, optional)

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

Transitioning `status` to `deceased` emits a MORTALITY event; `died_at` (defaults to now) and `cause` are recorded on it. Transitioning `status` to `sold` emits an INCOME event; `sale_amount` is required, `sold_at` (defaults to now) and `buyer` are optional. Transitioning away from either state reverses its event. Death/sale fields are rejected unless the individual is (or is becoming) deceased/sold respectively.

**Request body:**
- `name` (string | null, optional)
- `tag` (string | null, optional)
- `birth_date` (string (date) | null, optional)
- `mother_id` (integer | null, optional)
- `father_id` (integer | null, optional)
- `status` ('active' | 'sold' | 'deceased' | 'archived' | null, optional)
- `extra` (object | null, optional)
- `acquired_at` (string (date-time) | null, optional)
- `acquisition_method` ('purchased' | 'born' | 'other' | null, optional)
- `amount` (number | string | null, optional)
- `died_at` (string (date-time) | null, optional)
- `cause` (string | null, optional)
- `sale_amount` (number | string | null, optional)
- `sold_at` (string (date-time) | null, optional)
- `buyer` (string | null, optional)

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
- `acquired_at` (string (date-time), optional)
- `acquisition_method` ('purchased' | 'born' | 'other', optional)
- `amount` (number | string | null, optional)

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
- `acquisition_event_id` (integer | null, required)
- `acquisition_expense_event_id` (integer | null, required)
- `mortality_event_id` (integer | null, required)
- `sale_event_id` (integer | null, required)
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
- `acquired_at` (string (date-time) | null, optional)
- `acquisition_method` ('purchased' | 'born' | 'other' | null, optional)
- `amount` (number | string | null, optional)
- `died_at` (string (date-time) | null, optional)
- `cause` (string | null, optional)
- `sale_amount` (number | string | null, optional)
- `sold_at` (string (date-time) | null, optional)
- `buyer` (string | null, optional)

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

### AcquisitionMethod

**Values:** `purchased` | `born` | `other`

### IndividualStatus

**Values:** `active` | `sold` | `deceased` | `archived`

