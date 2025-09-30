import { Static, Type } from '@sinclair/typebox';
import { createPostEndpointSchema } from '../../utils/schema-builder';

const SpeciesTranslationSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	speciesId: Type.Integer({ minimum: 1 }),
	language: Type.String({ minLength: 2, maxLength: 2 }),
	name: Type.String({ minLength: 1 }),
	createdAt: Type.String({ format: 'date-time' }),
	updatedAt: Type.String({ format: 'date-time' }),
}, {
	$id: 'speciesTranslation',
	additionalProperties: false,
});

export const SpeciesTranslationCreateSchema = Type.Object({
	speciesId: Type.Integer({ minimum: 1 }),
	language: Type.String({ minLength: 2, maxLength: 2 }),
	name: Type.String({ minLength: 1 }),
}, {
	$id: 'speciesTranslationCreate',
	additionalProperties: false,
});

export const SpeciesTranslationResponseSchema = Type.Object({
	id: Type.String(),
	speciesId: Type.Optional(Type.String()),
	language: Type.String({ minLength: 2, maxLength: 2 }),
	name: Type.String({ minLength: 1 }),
	createdAt: Type.String({ format: 'date-time' }),
	updatedAt: Type.String({ format: 'date-time' }),
}, {
	$id: 'speciesTranslationResponse',
	additionalProperties: false,
});

export type SpeciesTranslation = Static<typeof SpeciesTranslationSchema>;
export type CreateSpeciesTranslation = Static<typeof SpeciesTranslationCreateSchema>;
export type SpeciesTranslationResponse = Static<typeof SpeciesTranslationResponseSchema>;

export const createSpeciesTranslationSchema = createPostEndpointSchema({
	body: SpeciesTranslationCreateSchema,
	dataSchema: SpeciesTranslationSchema,
	errorCodes: [400, 409],
});
