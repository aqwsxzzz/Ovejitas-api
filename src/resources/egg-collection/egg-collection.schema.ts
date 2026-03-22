import { Static, Type } from '@sinclair/typebox';
import {
	createListEndpointSchema,
	createPostEndpointSchema,
	createUpdateEndpointSchema,
	createDeleteEndpointSchema,
} from '../../utils/schema-builder';
import { PaginationQueryProps } from '../../utils/pagination';

const EggCollectionSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	flockId: Type.Integer(),
	date: Type.String(),
	totalEggs: Type.Integer(),
	brokenEggs: Type.Integer(),
	collectedBy: Type.Optional(Type.Union([Type.Integer(), Type.Null()])),
	notes: Type.Optional(Type.Union([Type.String(), Type.Null()])),
	createdAt: Type.String(),
	updatedAt: Type.String(),
}, {
	$id: 'eggCollection',
	additionalProperties: false,
});

export const EggCollectionResponseSchema = Type.Object({
	...EggCollectionSchema.properties,
	id: Type.String(),
	flockId: Type.String(),
	collectedBy: Type.Optional(Type.Union([Type.String(), Type.Null()])),
	usableEggs: Type.Integer(),
	layRate: Type.Number(),
}, {
	$id: 'eggCollectionResponse',
	additionalProperties: false,
});

export const EggCollectionCreateSchema = Type.Object({
	date: Type.String(),
	totalEggs: Type.Integer({ minimum: 0 }),
	brokenEggs: Type.Optional(Type.Integer({ minimum: 0 })),
	notes: Type.Optional(Type.String()),
}, {
	$id: 'eggCollectionCreate',
	additionalProperties: false,
});

export const EggCollectionUpdateSchema = Type.Object({
	totalEggs: Type.Optional(Type.Integer({ minimum: 0 })),
	brokenEggs: Type.Optional(Type.Integer({ minimum: 0 })),
	notes: Type.Optional(Type.String()),
}, {
	$id: 'eggCollectionUpdate',
	additionalProperties: false,
});

const EggCollectionParamsSchema = Type.Object({
	flockId: Type.String(),
});

const EggCollectionItemParamsSchema = Type.Object({
	flockId: Type.String(),
	id: Type.String(),
});

const EggCollectionQuerySchema = Type.Object({
	...PaginationQueryProps,
}, {
	$id: 'eggCollectionQuery',
	additionalProperties: false,
});

export type EggCollection = Static<typeof EggCollectionSchema>;
export type EggCollectionResponse = Static<typeof EggCollectionResponseSchema>;
export type EggCollectionCreate = Static<typeof EggCollectionCreateSchema>;
export type EggCollectionUpdate = Static<typeof EggCollectionUpdateSchema>;
export type EggCollectionParams = Static<typeof EggCollectionParamsSchema>;
export type EggCollectionItemParams = Static<typeof EggCollectionItemParamsSchema>;
export type EggCollectionQuery = Static<typeof EggCollectionQuerySchema>;

export const listEggCollectionsSchema = createListEndpointSchema({
	params: EggCollectionParamsSchema,
	querystring: EggCollectionQuerySchema,
	dataSchema: Type.Array(EggCollectionResponseSchema),
	errorCodes: [404],
});

export const createEggCollectionSchema = createPostEndpointSchema({
	params: EggCollectionParamsSchema,
	body: EggCollectionCreateSchema,
	dataSchema: EggCollectionResponseSchema,
	errorCodes: [400, 404, 409],
});

export const updateEggCollectionSchema = createUpdateEndpointSchema({
	params: EggCollectionItemParamsSchema,
	body: EggCollectionUpdateSchema,
	dataSchema: EggCollectionResponseSchema,
	errorCodes: [400, 404],
});

export const deleteEggCollectionSchema = createDeleteEndpointSchema({
	params: EggCollectionItemParamsSchema,
	errorCodes: [404],
});
