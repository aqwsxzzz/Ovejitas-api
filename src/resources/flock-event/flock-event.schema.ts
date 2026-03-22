import { Static, Type } from '@sinclair/typebox';
import {
	createListEndpointSchema,
	createPostEndpointSchema,
	createDeleteEndpointSchema,
} from '../../utils/schema-builder';
import { PaginationQueryProps } from '../../utils/pagination';

export enum FlockEventType {
	Mortality = 'mortality',
	Sale = 'sale',
	Cull = 'cull',
	Addition = 'addition',
	Transfer = 'transfer',
}

const FlockEventSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	flockId: Type.Integer(),
	eventType: Type.Enum(FlockEventType),
	count: Type.Integer(),
	date: Type.String(),
	reason: Type.Optional(Type.Union([Type.String(), Type.Null()])),
	recordedBy: Type.Optional(Type.Union([Type.Integer(), Type.Null()])),
	createdAt: Type.String(),
	updatedAt: Type.String(),
}, {
	$id: 'flockEvent',
	additionalProperties: false,
});

export const FlockEventResponseSchema = Type.Object({
	...FlockEventSchema.properties,
	id: Type.String(),
	flockId: Type.String(),
	recordedBy: Type.Optional(Type.Union([Type.String(), Type.Null()])),
}, {
	$id: 'flockEventResponse',
	additionalProperties: false,
});

export const FlockEventCreateSchema = Type.Object({
	eventType: Type.Enum(FlockEventType),
	count: Type.Integer({ minimum: 1 }),
	date: Type.String(),
	reason: Type.Optional(Type.String()),
}, {
	$id: 'flockEventCreate',
	additionalProperties: false,
});

const FlockEventParamsSchema = Type.Object({
	flockId: Type.String(),
});

const FlockEventDeleteParamsSchema = Type.Object({
	flockId: Type.String(),
	id: Type.String(),
});

const FlockEventQuerySchema = Type.Object({
	...PaginationQueryProps,
}, {
	$id: 'flockEventQuery',
	additionalProperties: false,
});

export type FlockEvent = Static<typeof FlockEventSchema>;
export type FlockEventResponse = Static<typeof FlockEventResponseSchema>;
export type FlockEventCreate = Static<typeof FlockEventCreateSchema>;
export type FlockEventParams = Static<typeof FlockEventParamsSchema>;
export type FlockEventDeleteParams = Static<typeof FlockEventDeleteParamsSchema>;
export type FlockEventQuery = Static<typeof FlockEventQuerySchema>;

export const listFlockEventsSchema = createListEndpointSchema({
	params: FlockEventParamsSchema,
	querystring: FlockEventQuerySchema,
	dataSchema: Type.Array(FlockEventResponseSchema),
	errorCodes: [404],
});

export const createFlockEventSchema = createPostEndpointSchema({
	params: FlockEventParamsSchema,
	body: FlockEventCreateSchema,
	dataSchema: FlockEventResponseSchema,
	errorCodes: [400, 404],
});

export const deleteFlockEventSchema = createDeleteEndpointSchema({
	params: FlockEventDeleteParamsSchema,
	errorCodes: [404],
});
