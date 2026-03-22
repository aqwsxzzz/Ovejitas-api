import { Static, Type } from '@sinclair/typebox';
import {
	createGetEndpointSchema,
	createListEndpointSchema,
	createPostEndpointSchema,
	createUpdateEndpointSchema,
	createDeleteEndpointSchema,
	createEndpointSchema,
} from '../../utils/schema-builder';
import { PaginationQueryProps } from '../../utils/pagination';

export const TransactionType = {
	Expense: 'expense',
	Income: 'income',
} as const;

export type TransactionTypeValue = (typeof TransactionType)[keyof typeof TransactionType];

const TransactionTypeEnum = Type.Union([
	Type.Literal(TransactionType.Expense),
	Type.Literal(TransactionType.Income),
]);

const FinancialTransactionSchema = Type.Object(
	{
		id: Type.Integer({ minimum: 1 }),
		farmId: Type.Integer(),
		type: TransactionTypeEnum,
		amount: Type.Number(),
		description: Type.Union([Type.String(), Type.Null()]),
		speciesId: Type.Integer(),
		date: Type.String(),
		createdBy: Type.Integer(),
		createdAt: Type.String(),
		updatedAt: Type.String(),
	},
	{
		$id: 'financialTransaction',
		additionalProperties: false,
	},
);

export const FinancialTransactionResponseSchema = Type.Object(
	{
		id: Type.String(),
		farmId: Type.String(),
		type: TransactionTypeEnum,
		amount: Type.Number(),
		description: Type.Union([Type.String(), Type.Null()]),
		speciesId: Type.String(),
		date: Type.String(),
		createdBy: Type.String(),
		createdAt: Type.String(),
		updatedAt: Type.String(),
	},
	{
		$id: 'financialTransactionResponse',
		additionalProperties: false,
	},
);

export const FinancialTransactionCreateSchema = Type.Object(
	{
		type: TransactionTypeEnum,
		amount: Type.Number({ minimum: 0.01 }),
		description: Type.Optional(Type.String()),
		speciesId: Type.String(),
		date: Type.String(),
	},
	{
		$id: 'financialTransactionCreate',
		additionalProperties: false,
	},
);

export const FinancialTransactionUpdateSchema = Type.Object(
	{
		type: Type.Optional(TransactionTypeEnum),
		amount: Type.Optional(Type.Number({ minimum: 0.01 })),
		description: Type.Optional(Type.String()),
		speciesId: Type.Optional(Type.String()),
		date: Type.Optional(Type.String()),
	},
	{
		$id: 'financialTransactionUpdate',
		additionalProperties: false,
	},
);

const FinancialTransactionQuerySchema = Type.Object(
	{
		type: Type.Optional(TransactionTypeEnum),
		speciesId: Type.Optional(Type.String()),
		from: Type.Optional(Type.String({ format: 'date' })),
		to: Type.Optional(Type.String({ format: 'date' })),
		...PaginationQueryProps,
	},
	{
		$id: 'financialTransactionQuery',
		additionalProperties: false,
	},
);

const FinancialTransactionParamsSchema = Type.Object({
	id: Type.String(),
});

const SummaryGroupBy = Type.Union([
	Type.Literal('day'),
	Type.Literal('week'),
	Type.Literal('month'),
	Type.Literal('year'),
]);

const FinancialTransactionSummaryQuerySchema = Type.Object(
	{
		groupBy: Type.Optional(SummaryGroupBy),
		type: Type.Optional(TransactionTypeEnum),
		speciesId: Type.Optional(Type.String()),
		from: Type.Optional(Type.String({ format: 'date' })),
		to: Type.Optional(Type.String({ format: 'date' })),
		period: Type.Optional(Type.String({ pattern: '^\\d+(d|w|m|y)$' })),
	},
	{
		$id: 'financialTransactionSummaryQuery',
		additionalProperties: false,
	},
);

const SummaryBreakdownItem = Type.Object({
	period: Type.String(),
	income: Type.Number(),
	expenses: Type.Number(),
	net: Type.Number(),
});

const SummaryResponseData = Type.Object({
	totals: Type.Object({
		income: Type.Number(),
		expenses: Type.Number(),
		net: Type.Number(),
	}),
	breakdown: Type.Array(SummaryBreakdownItem),
});

export type FinancialTransaction = Static<typeof FinancialTransactionSchema>;
export type FinancialTransactionResponse = Static<typeof FinancialTransactionResponseSchema>;
export type FinancialTransactionCreate = Static<typeof FinancialTransactionCreateSchema>;
export type FinancialTransactionUpdate = Static<typeof FinancialTransactionUpdateSchema>;
export type FinancialTransactionQuery = Static<typeof FinancialTransactionQuerySchema>;
export type FinancialTransactionParams = Static<typeof FinancialTransactionParamsSchema>;
export type FinancialTransactionSummaryQuery = Static<typeof FinancialTransactionSummaryQuerySchema>;
export type SummaryGroupByValue = Static<typeof SummaryGroupBy>;

export const listFinancialTransactionsSchema = createListEndpointSchema({
	querystring: FinancialTransactionQuerySchema,
	dataSchema: Type.Array(FinancialTransactionResponseSchema),
	errorCodes: [404],
});

export const getFinancialTransactionSchema = createGetEndpointSchema({
	params: FinancialTransactionParamsSchema,
	dataSchema: FinancialTransactionResponseSchema,
	errorCodes: [404],
});

export const createFinancialTransactionSchema = createPostEndpointSchema({
	body: FinancialTransactionCreateSchema,
	dataSchema: FinancialTransactionResponseSchema,
	errorCodes: [400, 404],
});

export const updateFinancialTransactionSchema = createUpdateEndpointSchema({
	params: FinancialTransactionParamsSchema,
	body: FinancialTransactionUpdateSchema,
	dataSchema: FinancialTransactionResponseSchema,
	errorCodes: [400, 404],
});

export const deleteFinancialTransactionSchema = createDeleteEndpointSchema({
	params: FinancialTransactionParamsSchema,
	errorCodes: [404],
});

export const summaryFinancialTransactionSchema = createEndpointSchema({
	querystring: FinancialTransactionSummaryQuerySchema,
	successCode: 200,
	dataSchema: SummaryResponseData,
	errorCodes: [400],
});
