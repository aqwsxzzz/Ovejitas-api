import {  Static, Type } from '@sinclair/typebox';
import { createPostEndpointSchema } from '../../utils/schema-builder';

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
	translationId: Type.String(),
}, {
	$id: 'speciesResponse',
	additionalProperties: false,
});

export type Species = Static<typeof SpeciesSchema>;
export type SpeciesCreateInput = Static<typeof SpeciesCreateSchema>;
export type SpeciesResponse = Static<typeof SpeciesResponseSchema>;

export const speciesSchemas = [SpeciesCreateSchema, SpeciesResponseSchema];

export const createSpeciesSchema = createPostEndpointSchema({
	body: SpeciesCreateSchema,
	dataSchema: SpeciesSchema,
	errorCodes: [400, 409],
});
