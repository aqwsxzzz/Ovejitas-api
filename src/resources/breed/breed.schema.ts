import { Type, Static } from '@sinclair/typebox';
import { createPostEndpointSchema, createUpdateEndpointSchema, createGetEndpointSchema } from '../../utils/schema-builder';

const BreedSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	speciesId: Type.Integer({ minimum: 1 }),
	name: Type.String(),
	createdAt: Type.Optional(Type.String()),
	updatedAt: Type.Optional(Type.String()),
}, {
	$id: 'breed',
	additionalProperties: false,
});

const BreedCreateSchema = Type.Object({
	name: Type.String(),
	speciesId: Type.String(),
}, {
	$id: 'breedCreate',
	additionalProperties: false,
});

const BreedUpdateSchema = Type.Object({
	name: Type.String(),
}, {
	$id: 'breedUpdate',
	additionalProperties: false,
});

export const BreedResponseSchema = Type.Object({
	...BreedSchema.properties,
	id: Type.String(),
	speciesId: Type.String(),

}, {
	$id: 'breedResponse',
	additionalProperties: false,
});

const BreedParamsSchema = Type.Object({
	id: Type.String(),
});

const BreedQuerySchema = Type.Object({
	speciesId: Type.String(),
	order: Type.Optional(Type.String()),
}, {
	$id: 'breedQuery',
	additionalProperties: false,
});

export type Breed = Static<typeof BreedSchema>;
export type BreedCreate = Static<typeof BreedCreateSchema>;
export type BreedResponse = Static<typeof BreedResponseSchema>;
export type BreedUpdate = Static<typeof BreedUpdateSchema>;
export type BreedParams = Static<typeof BreedParamsSchema>;
export type BreedQuery = Static<typeof BreedQuerySchema>;

export const createBreedSchema = createPostEndpointSchema({
	body: BreedCreateSchema,
	dataSchema: BreedResponseSchema,
	errorCodes: [400, 409],
});

export const updateBreedSchema = createUpdateEndpointSchema({
	body: BreedUpdateSchema,
	dataSchema: BreedResponseSchema,
	params: BreedParamsSchema,
});

export const getBreedsSchema = createGetEndpointSchema({
	querystring: BreedQuerySchema,
	dataSchema: Type.Array(BreedResponseSchema),
	errorCodes: [400],
});
