import { Static, Type } from '@sinclair/typebox';
import {
	createGetEndpointSchema,
	createListEndpointSchema,
	createPostEndpointSchema,
	createUpdateEndpointSchema,
	createDeleteEndpointSchema,
} from '../../utils/schema-builder';
import { PaginationQueryProps } from '../../utils/pagination';

const FeedLotSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	farmId: Type.Integer(),
	feedTypeId: Type.Integer(),
	qtyPurchased: Type.Number(),
	qtyRemaining: Type.Number(),
	unitPrice: Type.Number(),
	purchasedAt: Type.String(),
	supplier: Type.Optional(Type.Union([Type.String(), Type.Null()])),
	notes: Type.Optional(Type.Union([Type.String(), Type.Null()])),
	createdBy: Type.Integer(),
	createdAt: Type.String(),
	updatedAt: Type.String(),
}, {
	$id: 'feedLot',
	additionalProperties: false,
});

export const FeedLotResponseSchema = Type.Object({
	...FeedLotSchema.properties,
	id: Type.String(),
	farmId: Type.String(),
	feedTypeId: Type.String(),
	createdBy: Type.String(),
}, {
	$id: 'feedLotResponse',
	additionalProperties: false,
});

export const FeedLotCreateSchema = Type.Object({
	feedTypeId: Type.String(),
	qtyPurchased: Type.Number({ exclusiveMinimum: 0 }),
	unitPrice: Type.Number({ minimum: 0 }),
	purchasedAt: Type.String({ format: 'date' }),
	supplier: Type.Optional(Type.String({ maxLength: 255 })),
	notes: Type.Optional(Type.String()),
}, {
	$id: 'feedLotCreate',
	additionalProperties: false,
});

export const FeedLotUpdateSchema = Type.Object({
	unitPrice: Type.Optional(Type.Number({ minimum: 0 })),
	supplier: Type.Optional(Type.String({ maxLength: 255 })),
	notes: Type.Optional(Type.String()),
	purchasedAt: Type.Optional(Type.String({ format: 'date' })),
}, {
	$id: 'feedLotUpdate',
	additionalProperties: false,
});

export const FeedLotQuerySchema = Type.Object({
	feedTypeId: Type.Optional(Type.String()),
	hasStock: Type.Optional(Type.Boolean()),
	...PaginationQueryProps,
}, {
	$id: 'feedLotQuery',
	additionalProperties: false,
});

export const FeedLotParamsSchema = Type.Object({
	id: Type.String(),
});

export type FeedLot = Static<typeof FeedLotSchema>;
export type FeedLotResponse = Static<typeof FeedLotResponseSchema>;
export type FeedLotCreate = Static<typeof FeedLotCreateSchema>;
export type FeedLotUpdate = Static<typeof FeedLotUpdateSchema>;
export type FeedLotQuery = Static<typeof FeedLotQuerySchema>;
export type FeedLotParams = Static<typeof FeedLotParamsSchema>;

export const listFeedLotsSchema = createListEndpointSchema({
	querystring: FeedLotQuerySchema,
	dataSchema: Type.Array(FeedLotResponseSchema),
	errorCodes: [400],
});

export const getFeedLotByIdSchema = createGetEndpointSchema({
	params: FeedLotParamsSchema,
	dataSchema: FeedLotResponseSchema,
	errorCodes: [400, 404],
});

export const createFeedLotSchema = createPostEndpointSchema({
	body: FeedLotCreateSchema,
	dataSchema: FeedLotResponseSchema,
	errorCodes: [400, 404],
});

export const updateFeedLotSchema = createUpdateEndpointSchema({
	params: FeedLotParamsSchema,
	body: FeedLotUpdateSchema,
	dataSchema: FeedLotResponseSchema,
	errorCodes: [400, 404, 422],
});

export const deleteFeedLotSchema = createDeleteEndpointSchema({
	params: FeedLotParamsSchema,
	errorCodes: [400, 404, 409],
});
