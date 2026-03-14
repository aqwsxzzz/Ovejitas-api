import { Static, Type } from '@sinclair/typebox';
import { createPostEndpointSchema } from '../../utils/schema-builder';

const BreedTranslationSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	breedId: Type.Integer({ minimum: 1 }),
	language: Type.String({ minLength: 2, maxLength: 2 }),
	name: Type.String({ minLength: 1 }),
	createdAt: Type.String({ format: 'date-time' }),
	updatedAt: Type.String({ format: 'date-time' }),
}, {
	$id: 'breedTranslation',
	additionalProperties: false,
});

export const BreedTranslationCreateSchema = Type.Object({
	breedId: Type.String(),
	language: Type.String({ minLength: 2, maxLength: 2 }),
	name: Type.String({ minLength: 1 }),
}, {
	$id: 'breedTranslationCreate',
	additionalProperties: false,
});

export const BreedTranslationResponseSchema = Type.Object({
	...BreedTranslationSchema.properties,
	id: Type.String(),
	breedId: Type.String(),
}, {
	$id: 'breedTranslationResponse',
	additionalProperties: false,
});

export type BreedTranslation = Static<typeof BreedTranslationSchema>;
export type CreateBreedTranslation = Static<typeof BreedTranslationCreateSchema>;
export type BreedTranslationResponse = Static<typeof BreedTranslationResponseSchema>;

export const createBreedTranslationSchema = createPostEndpointSchema({
	body: BreedTranslationCreateSchema,
	dataSchema: BreedTranslationResponseSchema,
	errorCodes: [400, 409],
});
