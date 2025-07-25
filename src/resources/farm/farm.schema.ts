import { Static, Type } from '@sinclair/typebox';
import { createDeleteEndpointSchema, createGetEndpointSchema, createPostEndpointSchema } from '../../utils/schema-builder';

export const FarmSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	name: Type.String({ minLength: 1 }),
	createdAt: Type.String({ format: 'date-time' }),
	updatedAt: Type.String({ format: 'date-time' }),
}, {
	$id: 'farm',
	additionalProperties: false,
});

const FarmParamsSchema = Type.Object({
	farmId: Type.Integer({ minimum: 1 }),
}, {
	$id: 'farmParams',
	additionalProperties: false,
});

const FarmCreateSchema = Type.Pick(FarmSchema, ['name'], {
	$id: 'farmCreate',
	additionalProperties: false,
});

const FarmUpdateSchema = Type.Pick(FarmSchema, ['name'], {
	$id: 'farmUpdate',
	additionalProperties: false,
});

const FarmResponseSchema = Type.Object({
	...FarmSchema.properties,
	id: Type.String(),
}, {
	$id: 'farmResponse',
	additionalProperties: false,
});

export type Farm = Static<typeof FarmSchema>;
export type FarmCreateInput = Static<typeof FarmCreateSchema>;
export type FarmUpdateInput = Static<typeof FarmUpdateSchema>;
export type FarmResponse = Static<typeof FarmResponseSchema>;
export type FarmParams = Static<typeof FarmParamsSchema>;

export const createFarmSchema = createPostEndpointSchema({
	body: FarmCreateSchema,
	dataSchema: FarmResponseSchema,
	errorCodes: [400, 409],
});

export const updateFarmSchema = createPostEndpointSchema({
	params: FarmParamsSchema,
	body: FarmUpdateSchema,
	dataSchema: FarmResponseSchema,
	errorCodes: [400, 404],
});

export const getFarmSchema = createGetEndpointSchema({
	params: FarmParamsSchema,
	dataSchema: FarmResponseSchema,
	errorCodes: [404],
});

export const deleteFarmSchema = createDeleteEndpointSchema({
	params: FarmParamsSchema,
	errorCodes: [404],
});
