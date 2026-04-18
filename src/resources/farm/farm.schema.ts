import { Static, Type } from '@sinclair/typebox';
import { createDeleteEndpointSchema, createGetEndpointSchema, createListEndpointSchema, createPostEndpointSchema } from '../../utils/schema-builder';
import { PaginationQueryProps } from '../../utils/pagination';
import { CURRENCY_CODES } from './currencies';

const CurrencyEnum = Type.Union(
	CURRENCY_CODES.map(code => Type.Literal(code)),
);

export const FarmSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	name: Type.String({ minLength: 1 }),
	latitude: Type.Union([Type.Number({ minimum: -90, maximum: 90 }), Type.Null()]),
	longitude: Type.Union([Type.Number({ minimum: -180, maximum: 180 }), Type.Null()]),
	currency: Type.Union([CurrencyEnum, Type.Null()]),
	createdAt: Type.String({ format: 'date-time' }),
	updatedAt: Type.String({ format: 'date-time' }),
}, {
	$id: 'farm',
	additionalProperties: false,
});

const FarmParamsSchema = Type.Object({
	farmId: Type.String({ minimum: 1 }),
}, {
	$id: 'farmParams',
	additionalProperties: false,
});

const FarmCreateSchema = Type.Object({
	name: Type.String({ minLength: 1 }),
}, {
	$id: 'farmCreate',
	additionalProperties: false,
});

const FarmUpdateSchema = Type.Object({
	name: Type.Optional(Type.String({ minLength: 1 })),
	latitude: Type.Optional(Type.Union([Type.Number({ minimum: -90, maximum: 90 }), Type.Null()])),
	longitude: Type.Optional(Type.Union([Type.Number({ minimum: -180, maximum: 180 }), Type.Null()])),
	currency: Type.Optional(Type.Union([CurrencyEnum, Type.Null()])),
}, {
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

const FarmListQuerySchema = Type.Object({
	...PaginationQueryProps,
}, {
	$id: 'farmListQuery',
	additionalProperties: false,
});

const CurrencyOptionSchema = Type.Object({
	code: Type.String(),
	name: Type.String(),
	symbol: Type.String(),
}, { additionalProperties: false });

export type Farm = Static<typeof FarmSchema>;
export type FarmCreateInput = Static<typeof FarmCreateSchema>;
export type FarmUpdateInput = Static<typeof FarmUpdateSchema>;
export type FarmResponse = Static<typeof FarmResponseSchema>;
export type FarmParams = Static<typeof FarmParamsSchema>;
export type FarmListQuery = Static<typeof FarmListQuerySchema>;

export const createFarmSchema = createPostEndpointSchema({
	body: FarmCreateSchema,
	dataSchema: FarmResponseSchema,
	errorCodes: [400, 409],
});

export const updateFarmSchema = createPostEndpointSchema({
	params: FarmParamsSchema,
	body: FarmUpdateSchema,
	dataSchema: FarmResponseSchema,
	errorCodes: [400, 403, 404],
});

export const getFarmSchema = createGetEndpointSchema({
	params: FarmParamsSchema,
	dataSchema: FarmResponseSchema,
	errorCodes: [404],
});

export const listFarmsSchema = createListEndpointSchema({
	querystring: FarmListQuerySchema,
	dataSchema: Type.Array(FarmResponseSchema),
	errorCodes: [404],
});

export const deleteFarmSchema = createDeleteEndpointSchema({
	params: FarmParamsSchema,
	errorCodes: [404],
});

export const listCurrenciesSchema = createListEndpointSchema({
	dataSchema: Type.Array(CurrencyOptionSchema),
	errorCodes: [400],
});
