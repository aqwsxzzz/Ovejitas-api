import { Static, Type } from '@sinclair/typebox';
import {
	createGetEndpointSchema,
	createListEndpointSchema,
	createPostEndpointSchema,
	createUpdateEndpointSchema,
	createDeleteEndpointSchema,
} from '../../utils/schema-builder';
import { PaginationQueryProps } from '../../utils/pagination';

const FeedTypeSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	farmId: Type.Integer(),
	name: Type.String(),
	notes: Type.Optional(Type.Union([Type.String(), Type.Null()])),
	createdAt: Type.String(),
	updatedAt: Type.String(),
}, {
	$id: 'feedType',
	additionalProperties: false,
});

export const FeedTypeResponseSchema = Type.Object({
	...FeedTypeSchema.properties,
	id: Type.String(),
	farmId: Type.String(),
}, {
	$id: 'feedTypeResponse',
	additionalProperties: false,
});

export const FeedTypeCreateSchema = Type.Object({
	name: Type.String({ minLength: 1, maxLength: 120 }),
	notes: Type.Optional(Type.String()),
}, {
	$id: 'feedTypeCreate',
	additionalProperties: false,
});

export const FeedTypeUpdateSchema = Type.Object({
	name: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
	notes: Type.Optional(Type.String()),
}, {
	$id: 'feedTypeUpdate',
	additionalProperties: false,
});

export const FeedTypeQuerySchema = Type.Object({
	...PaginationQueryProps,
}, {
	$id: 'feedTypeQuery',
	additionalProperties: false,
});

export const FeedTypeParamsSchema = Type.Object({
	id: Type.String(),
});

export type FeedType = Static<typeof FeedTypeSchema>;
export type FeedTypeResponse = Static<typeof FeedTypeResponseSchema>;
export type FeedTypeCreate = Static<typeof FeedTypeCreateSchema>;
export type FeedTypeUpdate = Static<typeof FeedTypeUpdateSchema>;
export type FeedTypeQuery = Static<typeof FeedTypeQuerySchema>;
export type FeedTypeParams = Static<typeof FeedTypeParamsSchema>;

export const listFeedTypesSchema = createListEndpointSchema({
	querystring: FeedTypeQuerySchema,
	dataSchema: Type.Array(FeedTypeResponseSchema),
	errorCodes: [400],
});

export const getFeedTypeByIdSchema = createGetEndpointSchema({
	params: FeedTypeParamsSchema,
	dataSchema: FeedTypeResponseSchema,
	errorCodes: [400, 404],
});

export const createFeedTypeSchema = createPostEndpointSchema({
	body: FeedTypeCreateSchema,
	dataSchema: FeedTypeResponseSchema,
	errorCodes: [400, 409],
});

export const updateFeedTypeSchema = createUpdateEndpointSchema({
	params: FeedTypeParamsSchema,
	body: FeedTypeUpdateSchema,
	dataSchema: FeedTypeResponseSchema,
	errorCodes: [400, 404],
});

export const deleteFeedTypeSchema = createDeleteEndpointSchema({
	params: FeedTypeParamsSchema,
	errorCodes: [400, 404, 409],
});
