import { Static, Type } from '@sinclair/typebox';
import {
	createGetEndpointSchema,
	createListEndpointSchema,
	createPostEndpointSchema,
} from '../../utils/schema-builder';

const EggPricingSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	farmId: Type.Integer(),
	pricePerEgg: Type.Number(),
	effectiveFrom: Type.String(),
	effectiveTo: Type.Union([Type.String(), Type.Null()]),
	createdAt: Type.String(),
	updatedAt: Type.String(),
}, {
	$id: 'eggPricing',
	additionalProperties: false,
});

export const EggPricingResponseSchema = Type.Object({
	id: Type.String(),
	farmId: Type.String(),
	pricePerEgg: Type.Number(),
	currency: Type.Union([Type.String(), Type.Null()]),
	effectiveFrom: Type.String(),
	effectiveTo: Type.Union([Type.String(), Type.Null()]),
	createdAt: Type.String(),
	updatedAt: Type.String(),
}, {
	$id: 'eggPricingResponse',
	additionalProperties: false,
});

export const EggPricingCreateSchema = Type.Object({
	pricePerEgg: Type.Number({ minimum: 0, exclusiveMinimum: 0 }),
	effectiveFrom: Type.Optional(Type.String({ format: 'date' })),
}, {
	$id: 'eggPricingCreate',
	additionalProperties: false,
});

export type EggPricing = Static<typeof EggPricingSchema>;
export type EggPricingResponse = Static<typeof EggPricingResponseSchema>;
export type EggPricingCreate = Static<typeof EggPricingCreateSchema>;

export const getActiveEggPricingSchema = createGetEndpointSchema({
	dataSchema: EggPricingResponseSchema,
	errorCodes: [404],
});

export const getEggPricingHistorySchema = createListEndpointSchema({
	dataSchema: Type.Array(EggPricingResponseSchema),
	errorCodes: [400],
});

export const createEggPricingSchema = createPostEndpointSchema({
	body: EggPricingCreateSchema,
	dataSchema: EggPricingResponseSchema,
	errorCodes: [400, 409],
});
