
import {  Static, Type } from '@sinclair/typebox';
import { createGetEndpointSchema, createPostEndpointSchema } from '../../utils/schema-builder';
import { SpeciesTranslationResponseSchema } from '../species-translation/species-translation.schema';
import { UserLanguage } from '../user/user.schema';

const SpeciesSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	createdAt: Type.String({ format: 'date-time' }),
	updatedAt: Type.String({ format: 'date-time' }),
}, {
	$id: 'species',
	additionalProperties: false,
});

const SpeciesCreateSchema = Type.Object({
	name: Type.String({ minLength: 1 }),
	language: Type.String({ minLength: 2, maxLength: 2 }),
}, {
	$id: 'speciesCreate',
	additionalProperties: false,
});

export const SpeciesResponseSchema = Type.Object({
	...SpeciesSchema.properties,
	id: Type.String(),
	translationId: Type.Optional(Type.String()),
	translations: Type.Optional(Type.Array(SpeciesTranslationResponseSchema)),
}, {
	$id: 'speciesResponse',
	additionalProperties: false,
});

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const SpeciesParamsSchema = Type.Object({
	id: Type.String(),
}, {
	$id: 'speciesParams',
	additionalProperties: false,
});

const SpeciesQuerystringSchema = Type.Object({
	include: Type.Optional(Type.String()),
	order: Type.Optional(Type.String()),
	language: (Type.Enum(UserLanguage)),
}, {
	$id: 'speciesQuerystring',
	additionalProperties: false,
});

export type Species = Static<typeof SpeciesSchema>;
export type SpeciesCreateInput = Static<typeof SpeciesCreateSchema>;
export type SpeciesQueryString = Static<typeof SpeciesQuerystringSchema>;
export type SpeciesResponse = Static<typeof SpeciesResponseSchema>;
export type SpeciesParams = Static<typeof SpeciesParamsSchema>;

export const createSpeciesSchema = createPostEndpointSchema({
	body: SpeciesCreateSchema,
	dataSchema: SpeciesResponseSchema,
	errorCodes: [400, 409],
});

export const getSpeciesSchema = createGetEndpointSchema({
	querystring: SpeciesQuerystringSchema,
	dataSchema: SpeciesResponseSchema,
	errorCodes: [404],
});

export const listSpeciesSchema = createGetEndpointSchema({
	querystring: SpeciesQuerystringSchema,
	dataSchema: Type.Array(SpeciesResponseSchema),
	errorCodes: [404],
});
