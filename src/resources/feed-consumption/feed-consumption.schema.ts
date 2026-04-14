import { Static, Type } from '@sinclair/typebox';
import {
	createGetEndpointSchema,
	createListEndpointSchema,
	createPostEndpointSchema,
	createDeleteEndpointSchema,
} from '../../utils/schema-builder';
import { PaginationQueryProps } from '../../utils/pagination';

export enum FeedConsumptionReason {
	Feeding = 'feeding',
	Waste = 'waste',
	Transfer = 'transfer',
	Adjustment = 'adjustment',
}

const FeedConsumptionLotResponseSchema = Type.Object({
	id: Type.String(),
	lotId: Type.String(),
	qtyDrawn: Type.Number(),
	unitPriceSnapshot: Type.Number(),
}, {
	$id: 'feedConsumptionLotResponse',
	additionalProperties: false,
});

export const FeedConsumptionResponseSchema = Type.Object({
	id: Type.String(),
	farmId: Type.String(),
	flockId: Type.Union([Type.String(), Type.Null()]),
	feedTypeId: Type.String(),
	consumedAt: Type.String(),
	qty: Type.Number(),
	reason: Type.Enum(FeedConsumptionReason),
	notes: Type.Union([Type.String(), Type.Null()]),
	createdBy: Type.String(),
	totalCost: Type.Number(),
	lots: Type.Optional(Type.Array(FeedConsumptionLotResponseSchema)),
	createdAt: Type.String(),
	updatedAt: Type.String(),
}, {
	$id: 'feedConsumptionResponse',
	additionalProperties: false,
});

export const FeedConsumptionCreateSchema = Type.Object({
	flockId: Type.Optional(Type.Union([Type.String(), Type.Null()])),
	feedTypeId: Type.String(),
	consumedAt: Type.String({ format: 'date' }),
	qty: Type.Number({ exclusiveMinimum: 0 }),
	reason: Type.Enum(FeedConsumptionReason),
	notes: Type.Optional(Type.String()),
}, {
	$id: 'feedConsumptionCreate',
	additionalProperties: false,
});

export const FeedConsumptionQuerySchema = Type.Object({
	flockId: Type.Optional(Type.String()),
	feedTypeId: Type.Optional(Type.String()),
	from: Type.Optional(Type.String({ format: 'date' })),
	to: Type.Optional(Type.String({ format: 'date' })),
	include: Type.Optional(Type.String()),
	...PaginationQueryProps,
}, {
	$id: 'feedConsumptionQuery',
	additionalProperties: false,
});

export const FeedConsumptionParamsSchema = Type.Object({
	id: Type.String(),
});

export type FeedConsumptionResponse = Static<typeof FeedConsumptionResponseSchema>;
export type FeedConsumptionCreate = Static<typeof FeedConsumptionCreateSchema>;
export type FeedConsumptionQuery = Static<typeof FeedConsumptionQuerySchema>;
export type FeedConsumptionParams = Static<typeof FeedConsumptionParamsSchema>;

export const listFeedConsumptionsSchema = createListEndpointSchema({
	querystring: FeedConsumptionQuerySchema,
	dataSchema: Type.Array(FeedConsumptionResponseSchema),
	errorCodes: [400],
});

export const getFeedConsumptionByIdSchema = createGetEndpointSchema({
	params: FeedConsumptionParamsSchema,
	dataSchema: FeedConsumptionResponseSchema,
	errorCodes: [400, 404],
});

export const createFeedConsumptionSchema = createPostEndpointSchema({
	body: FeedConsumptionCreateSchema,
	dataSchema: FeedConsumptionResponseSchema,
	errorCodes: [400, 404, 422],
});

export const deleteFeedConsumptionSchema = createDeleteEndpointSchema({
	params: FeedConsumptionParamsSchema,
	errorCodes: [400, 404],
});
