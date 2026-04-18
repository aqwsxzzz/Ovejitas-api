import { Static, Type } from '@sinclair/typebox';
import { createGetEndpointSchema } from '../../utils/schema-builder';

const PeriodEnum = Type.Union([
	Type.Literal('daily'),
	Type.Literal('weekly'),
	Type.Literal('monthly'),
]);

export const FlockProfitabilityQuerySchema = Type.Object({
	period: PeriodEnum,
	from: Type.String({ format: 'date' }),
	to: Type.String({ format: 'date' }),
	flockId: Type.Optional(Type.String()),
}, {
	$id: 'flockProfitabilityQuery',
	additionalProperties: false,
});

const PeriodBreakdownSchema = Type.Object({
	period: Type.String(),
	eggsCollected: Type.Integer(),
	eggsSellable: Type.Integer(),
	brokenEggs: Type.Integer(),
	eggRevenue: Type.Number(),
	feedQuantity: Type.Number(),
	feedCost: Type.Number(),
	profit: Type.Number(),
	profitMargin: Type.Union([Type.Number(), Type.Null()]),
}, { additionalProperties: false });

const FlockRowSchema = Type.Object({
	flockId: Type.String(),
	flockName: Type.String(),
	speciesId: Type.String(),
	eggsCollected: Type.Integer(),
	eggsSellable: Type.Integer(),
	brokenEggs: Type.Integer(),
	eggsCollectedStacks: Type.Number(),
	totalEggRevenue: Type.Number(),
	feedQuantity: Type.Number(),
	totalFeedCost: Type.Number(),
	totalExpenses: Type.Number(),
	profit: Type.Number(),
	profitMargin: Type.Union([Type.Number(), Type.Null()]),
	costPerDozenEggs: Type.Union([Type.Number(), Type.Null()]),
	fcrKgPerDozen: Type.Union([Type.Number(), Type.Null()]),
	warnings: Type.Array(Type.String()),
	periodBreakdown: Type.Array(PeriodBreakdownSchema),
}, { additionalProperties: false });

export const FlockProfitabilityResponseSchema = Type.Object({
	farmId: Type.String(),
	currency: Type.Union([Type.String(), Type.Null()]),
	reportPeriod: PeriodEnum,
	dateRange: Type.Object({
		from: Type.String(),
		to: Type.String(),
	}),
	flocks: Type.Array(FlockRowSchema),
}, {
	$id: 'flockProfitabilityResponse',
	additionalProperties: false,
});

export type FlockProfitabilityQuery = Static<typeof FlockProfitabilityQuerySchema>;
export type FlockProfitabilityResponse = Static<typeof FlockProfitabilityResponseSchema>;
export type FlockProfitabilityPeriod = Static<typeof PeriodEnum>;

export const flockProfitabilitySchema = createGetEndpointSchema({
	querystring: FlockProfitabilityQuerySchema,
	dataSchema: FlockProfitabilityResponseSchema,
	errorCodes: [400, 404, 422],
});
