import { Type, Static } from '@sinclair/typebox';
import { createPostEndpointSchema } from '../../utils/schema-builder';

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

const BreedResponseSchema = Type.Object({
	...BreedSchema.properties,
	id: Type.String(),
	speciesId: Type.String(),

}, {
	$id: 'breedResponse',
	additionalProperties: false,
});

export type Breed = Static<typeof BreedSchema>;
export type BreedCreate = Static<typeof BreedCreateSchema>;
export type BreedResponse = Static<typeof BreedResponseSchema>;

export const breedSchemas = [BreedSchema, BreedCreateSchema];

export const createBreedSchema = createPostEndpointSchema({
	body: BreedCreateSchema,
	dataSchema: BreedResponseSchema,
	errorCodes: [400, 409],
});
