import { Type, Static } from '@sinclair/typebox';
import { createPostEndpointSchema, createGetEndpointSchema } from '../../utils/schema-builder';
import { BreedTranslationResponseSchema } from '../breed-translation/breed-translation.schema';
import { UserLanguage } from '../user/user.schema';

const BreedSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	speciesId: Type.Integer({ minimum: 1 }),
	createdAt: Type.Optional(Type.String()),
	updatedAt: Type.Optional(Type.String()),
}, {
	$id: 'breed',
	additionalProperties: false,
});

const BreedCreateSchema = Type.Object({
	name: Type.String({ minLength: 1 }),
	language: Type.String({ minLength: 2, maxLength: 2 }),
	speciesId: Type.String(),
}, {
	$id: 'breedCreate',
	additionalProperties: false,
});

export const BreedResponseSchema = Type.Object({
	...BreedSchema.properties,
	id: Type.String(),
	speciesId: Type.String(),
	translations: Type.Optional(Type.Array(BreedTranslationResponseSchema)),
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
	include: Type.Optional(Type.String()),
	language: Type.Optional(Type.Enum(UserLanguage)),
}, {
	$id: 'breedQuery',
	additionalProperties: false,
});

export type Breed = Static<typeof BreedSchema>;
export type BreedCreate = Static<typeof BreedCreateSchema>;
export type BreedResponse = Static<typeof BreedResponseSchema>;
export type BreedParams = Static<typeof BreedParamsSchema>;
export type BreedQuery = Static<typeof BreedQuerySchema>;

export const createBreedSchema = createPostEndpointSchema({
	body: BreedCreateSchema,
	dataSchema: BreedResponseSchema,
	errorCodes: [400, 409],
});

export const getBreedsSchema = createGetEndpointSchema({
	querystring: BreedQuerySchema,
	dataSchema: Type.Array(BreedResponseSchema),
	errorCodes: [400],
});
