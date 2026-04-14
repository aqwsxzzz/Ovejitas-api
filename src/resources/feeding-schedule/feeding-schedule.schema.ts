import { Static, Type } from '@sinclair/typebox';
import {
	createGetEndpointSchema,
	createListEndpointSchema,
	createPostEndpointSchema,
	createUpdateEndpointSchema,
	createDeleteEndpointSchema,
} from '../../utils/schema-builder';
import { PaginationQueryProps } from '../../utils/pagination';

const FeedingScheduleSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	farmId: Type.Integer(),
	flockId: Type.Integer(),
	feedTypeId: Type.Integer(),
	qtyPerDay: Type.Number(),
	activeFrom: Type.String(),
	activeTo: Type.Union([Type.String(), Type.Null()]),
	createdAt: Type.String(),
	updatedAt: Type.String(),
}, {
	$id: 'feedingSchedule',
	additionalProperties: false,
});

export const FeedingScheduleResponseSchema = Type.Object({
	...FeedingScheduleSchema.properties,
	id: Type.String(),
	farmId: Type.String(),
	flockId: Type.String(),
	feedTypeId: Type.String(),
}, {
	$id: 'feedingScheduleResponse',
	additionalProperties: false,
});

export const FeedingScheduleCreateSchema = Type.Object({
	flockId: Type.String(),
	feedTypeId: Type.String(),
	qtyPerDay: Type.Number({ exclusiveMinimum: 0 }),
	activeFrom: Type.String({ format: 'date' }),
	activeTo: Type.Optional(Type.Union([Type.String({ format: 'date' }), Type.Null()])),
}, {
	$id: 'feedingScheduleCreate',
	additionalProperties: false,
});

export const FeedingScheduleUpdateSchema = Type.Object({
	qtyPerDay: Type.Optional(Type.Number({ exclusiveMinimum: 0 })),
	activeFrom: Type.Optional(Type.String({ format: 'date' })),
	activeTo: Type.Optional(Type.Union([Type.String({ format: 'date' }), Type.Null()])),
}, {
	$id: 'feedingScheduleUpdate',
	additionalProperties: false,
});

export const FeedingScheduleQuerySchema = Type.Object({
	flockId: Type.Optional(Type.String()),
	feedTypeId: Type.Optional(Type.String()),
	activeOnly: Type.Optional(Type.Boolean()),
	...PaginationQueryProps,
}, {
	$id: 'feedingScheduleQuery',
	additionalProperties: false,
});

export const FeedingScheduleParamsSchema = Type.Object({
	id: Type.String(),
});

export type FeedingSchedule = Static<typeof FeedingScheduleSchema>;
export type FeedingScheduleResponse = Static<typeof FeedingScheduleResponseSchema>;
export type FeedingScheduleCreate = Static<typeof FeedingScheduleCreateSchema>;
export type FeedingScheduleUpdate = Static<typeof FeedingScheduleUpdateSchema>;
export type FeedingScheduleQuery = Static<typeof FeedingScheduleQuerySchema>;
export type FeedingScheduleParams = Static<typeof FeedingScheduleParamsSchema>;

export const listFeedingSchedulesSchema = createListEndpointSchema({
	querystring: FeedingScheduleQuerySchema,
	dataSchema: Type.Array(FeedingScheduleResponseSchema),
	errorCodes: [400],
});

export const getFeedingScheduleByIdSchema = createGetEndpointSchema({
	params: FeedingScheduleParamsSchema,
	dataSchema: FeedingScheduleResponseSchema,
	errorCodes: [400, 404],
});

export const createFeedingScheduleSchema = createPostEndpointSchema({
	body: FeedingScheduleCreateSchema,
	dataSchema: FeedingScheduleResponseSchema,
	errorCodes: [400, 404, 409],
});

export const updateFeedingScheduleSchema = createUpdateEndpointSchema({
	params: FeedingScheduleParamsSchema,
	body: FeedingScheduleUpdateSchema,
	dataSchema: FeedingScheduleResponseSchema,
	errorCodes: [400, 404, 409],
});

export const deleteFeedingScheduleSchema = createDeleteEndpointSchema({
	params: FeedingScheduleParamsSchema,
	errorCodes: [400, 404],
});
