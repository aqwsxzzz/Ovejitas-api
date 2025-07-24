
import {  Static, Type } from '@sinclair/typebox';
import { createGetEndpointSchema, createPostEndpointSchema } from '../../utils/schema-builder';
import { SpeciesTranslationResponseSchema } from '../species-translation/species-translation.schema';

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

const SpeciesResponseSchema = Type.Object({
	...SpeciesSchema.properties,
	id: Type.String(),
	translationId: Type.Optional(Type.String()),
	translations: Type.Optional(Type.Array(SpeciesTranslationResponseSchema)),
}, {
	$id: 'speciesResponse',
	additionalProperties: false,
});

const SpeciesIncludeSchema = Type.Object({
	include: Type.Optional(Type.String()),
}, {
	$id: 'speciesInclude',
	additionalProperties: false,
});

export type Species = Static<typeof SpeciesSchema>;
export type SpeciesCreateInput = Static<typeof SpeciesCreateSchema>;
export type SpeciesInclude = Static<typeof SpeciesIncludeSchema>;
export type SpeciesResponse = Static<typeof SpeciesResponseSchema>;

export const speciesSchemas = [SpeciesCreateSchema, SpeciesResponseSchema];

export const createSpeciesSchema = createPostEndpointSchema({
	body: SpeciesCreateSchema,
	dataSchema: SpeciesResponseSchema,
	errorCodes: [400, 409],
});

export const getSpeciesSchema = createGetEndpointSchema({
	querystring: SpeciesIncludeSchema,
	dataSchema: SpeciesResponseSchema,
	errorCodes: [404],
});

export const listSpeciesSchema = createGetEndpointSchema({
	querystring: SpeciesIncludeSchema,
	dataSchema: Type.Array(SpeciesResponseSchema),
	errorCodes: [404],
});
