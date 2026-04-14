import { Static, Type } from '@sinclair/typebox';
import {
	createGetEndpointSchema,
} from '../../utils/schema-builder';

export const CostByFlockQuerySchema = Type.Object({
	from: Type.Optional(Type.String({ format: 'date' })),
	to: Type.Optional(Type.String({ format: 'date' })),
	flockId: Type.Optional(Type.String()),
}, {
	$id: 'feedReportCostByFlockQuery',
	additionalProperties: false,
});

const FeedTypeBreakdownSchema = Type.Object({
	feedTypeId: Type.String(),
	totalQty: Type.Number(),
	totalCost: Type.Number(),
}, {
	additionalProperties: false,
});

const FlockCostSchema = Type.Object({
	flockId: Type.Union([Type.String(), Type.Null()]),
	totalQty: Type.Number(),
	totalCost: Type.Number(),
	byFeedType: Type.Array(FeedTypeBreakdownSchema),
}, {
	additionalProperties: false,
});

export const CostByFlockResponseSchema = Type.Object({
	from: Type.Union([Type.String(), Type.Null()]),
	to: Type.Union([Type.String(), Type.Null()]),
	flocks: Type.Array(FlockCostSchema),
}, {
	$id: 'feedReportCostByFlockResponse',
	additionalProperties: false,
});

export const CostByLotParamsSchema = Type.Object({
	lotId: Type.String(),
});

const FlockDrawdownSchema = Type.Object({
	flockId: Type.Union([Type.String(), Type.Null()]),
	totalQty: Type.Number(),
	totalCost: Type.Number(),
}, {
	additionalProperties: false,
});

export const CostByLotResponseSchema = Type.Object({
	lotId: Type.String(),
	feedTypeId: Type.String(),
	qtyPurchased: Type.Number(),
	qtyRemaining: Type.Number(),
	qtyDrawn: Type.Number(),
	totalCost: Type.Number(),
	byFlock: Type.Array(FlockDrawdownSchema),
}, {
	$id: 'feedReportCostByLotResponse',
	additionalProperties: false,
});

export type CostByFlockQuery = Static<typeof CostByFlockQuerySchema>;
export type CostByFlockResponse = Static<typeof CostByFlockResponseSchema>;
export type CostByLotParams = Static<typeof CostByLotParamsSchema>;
export type CostByLotResponse = Static<typeof CostByLotResponseSchema>;

export const costByFlockSchema = createGetEndpointSchema({
	querystring: CostByFlockQuerySchema,
	dataSchema: CostByFlockResponseSchema,
	errorCodes: [400],
});

export const costByLotSchema = createGetEndpointSchema({
	params: CostByLotParamsSchema,
	dataSchema: CostByLotResponseSchema,
	errorCodes: [400, 404],
});
