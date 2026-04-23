# assets

_Auto-generated. Do not edit by hand._

## GET /api/v1/farms/{farm_id}/assets

_List assets in a farm_

**Responses:**
- `200` → Page_AssetRead_ — Successful Response
- `422` → HTTPValidationError — Validation Error

## POST /api/v1/farms/{farm_id}/assets

_Create an asset in a farm_

**Request body:**
- `name` (string, required)
- `kind` (AssetKind, required)
- `mode` (AssetMode, required)
- `location` (string | null, optional)
- `description` (string | null, optional)

**Responses:**
- `201` → AssetRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/assets/{asset_id}

_Get one asset_

**Responses:**
- `200` → AssetRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## PATCH /api/v1/farms/{farm_id}/assets/{asset_id}

_Update an asset_

**Request body:**
- `name` (string | null, optional)
- `kind` (AssetKind | null, optional)
- `mode` (AssetMode | null, optional)
- `location` (string | null, optional)
- `description` (string | null, optional)

**Responses:**
- `200` → AssetRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## DELETE /api/v1/farms/{farm_id}/assets/{asset_id}

_Delete an asset_

**Responses:**
- `204` → any — Successful Response
- `422` → HTTPValidationError — Validation Error

