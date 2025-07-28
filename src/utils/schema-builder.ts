import { Type, TSchema } from '@sinclair/typebox';

/**
 * Common response schemas used across all API endpoints
 */
export const BaseResponseSchema = Type.Object({
	status: Type.String(),
	message: Type.String(),
});

export const SuccessResponseSchema = Type.Object({
	status: Type.String(),
	message: Type.String(),
	data: Type.Unknown(), // Will be overridden with specific data schema
	meta: Type.Optional(Type.Object({
		timestamp: Type.String(),
	})),
});

export const ErrorResponseSchema = Type.Object({
	status: Type.String(),
	message: Type.String(),
});

/**
 * Pre-defined error response schemas for common HTTP status codes
 */
export const CommonErrorResponses = {
	400: ErrorResponseSchema,
	404: ErrorResponseSchema,
	409: ErrorResponseSchema,
	500: ErrorResponseSchema,
} as const;

/**
 * Configuration interface for creating endpoint schemas
 */
export interface EndpointSchemaConfig {
    body?: TSchema
    params?: TSchema
    querystring?: TSchema
    successCode: 200 | 201 | 204
    dataSchema?: TSchema
    errorCodes?: (400 | 404 | 409 | 500)[]
}

/**
 * Creates a complete endpoint schema with consistent response structure
 *
 * @param config - Configuration object for the endpoint
 * @returns Complete Fastify schema object
 *
 * @example
 * ```typescript
 * const createUserSchema = createEndpointSchema({
 *     body: UserCreateSchema,
 *     successCode: 201,
 *     dataSchema: UserResponseSchema,
 *     errorCodes: [400, 409]
 * })
 * ```
 */
export const createEndpointSchema = (config: EndpointSchemaConfig) => {
	const schema: Record<string, TSchema | Record<string, TSchema>> = {};

	// Add request schemas if provided
	if (config.body) schema.body = config.body;
	if (config.params) schema.params = config.params;
	if (config.querystring) schema.querystring = config.querystring;

	// Build response schemas
	schema.response = {};

	// Add success response
	if (config.dataSchema) {
		schema.response[config.successCode] = Type.Object({
			status: Type.String(),
			message: Type.String(),
			data: config.dataSchema,
			meta: Type.Optional(Type.Object({
				timestamp: Type.String(),
			})),
		});
	} else {
		// For endpoints that don't return data (like delete)
		schema.response[config.successCode] = Type.Object({
			status: Type.String(),
			message: Type.String(),
			data: Type.Null(),
			meta: Type.Optional(Type.Object({
				timestamp: Type.String(),
			})),
		});
	}

	// Add error responses
	const errorCodes = config.errorCodes || [400];
	errorCodes.forEach(code => {
		schema.response[code] = CommonErrorResponses[code];
	});

	return schema;
};

/**
 * Creates a simple GET endpoint schema (no body, just params/querystring)
 */
export const createGetEndpointSchema = (config: Omit<EndpointSchemaConfig, 'body' | 'successCode'> & { params?: TSchema, querystring?: TSchema }) => {
	return createEndpointSchema({
		...config,
		successCode: 200,
	});
};

/**
 * Creates a POST endpoint schema (with body, returns 201)
 */
export const createPostEndpointSchema = (config: Omit<EndpointSchemaConfig, 'successCode'> & { body: TSchema }) => {
	return createEndpointSchema({
		...config,
		successCode: 201,
	});
};

/**
 * Creates a PUT/PATCH endpoint schema (with body and params, returns 200)
 */
export const createUpdateEndpointSchema = (config: Omit<EndpointSchemaConfig, 'successCode'> & { body: TSchema, params: TSchema }) => {
	return createEndpointSchema({
		...config,
		successCode: 200,
	});
};

/**
 * Creates a DELETE endpoint schema (with params, returns 200 with null data)
 */
export const createDeleteEndpointSchema = (config: Omit<EndpointSchemaConfig, 'successCode' | 'dataSchema'> & { params: TSchema }) => {
	return createEndpointSchema({
		...config,
		successCode: 200,
		dataSchema: Type.Null(),
	});
};
