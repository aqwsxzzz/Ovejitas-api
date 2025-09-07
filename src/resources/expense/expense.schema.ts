import { Static, Type } from '@sinclair/typebox';
import {
	createGetEndpointSchema,
	createPostEndpointSchema,
	createUpdateEndpointSchema,
	createDeleteEndpointSchema,
} from '../../utils/schema-builder';

export enum ExpenseCategory {
	Feed = 'feed',
	Veterinary = 'veterinary',
	Transport = 'transport',
	Equipment = 'equipment',
	Labor = 'labor',
	Utilities = 'utilities',
	Maintenance = 'maintenance',
	Other = 'other',
}

export enum PaymentMethod {
	Cash = 'cash',
	BankTransfer = 'bank_transfer',
	CreditCard = 'credit_card',
	DebitCard = 'debit_card',
	Check = 'check',
	Other = 'other',
}

export enum ExpenseStatus {
	Pending = 'pending',
	Paid = 'paid',
	Reimbursed = 'reimbursed',
}

export enum QuantityUnit {
	Kg = 'kg',
	Liters = 'liters',
	Units = 'units',
	Boxes = 'boxes',
	Bags = 'bags',
	Doses = 'doses',
	Hours = 'hours',
	Other = 'other',
}

const ExpenseSchema = Type.Object(
	{
		id: Type.Integer({ minimum: 1 }),
		farmId: Type.Integer(),
		date: Type.String(),
		amount: Type.Number(),
		description: Type.Optional(Type.String()),
		category: Type.Enum(ExpenseCategory),
		speciesId: Type.Optional(Type.Integer()),
		breedId: Type.Optional(Type.Integer()),
		animalId: Type.Optional(Type.Integer()),
		lotId: Type.Optional(Type.Integer()),
		vendor: Type.Optional(Type.String()),
		paymentMethod: Type.Optional(Type.Enum(PaymentMethod)),
		invoiceNumber: Type.Optional(Type.String()),
		quantity: Type.Optional(Type.Number()),
		quantityUnit: Type.Optional(Type.Enum(QuantityUnit)),
		unitCost: Type.Optional(Type.Number()),
		status: Type.Optional(Type.Enum(ExpenseStatus)),
		createdBy: Type.Integer(),
		createdAt: Type.String(),
		updatedAt: Type.String(),
	},
	{
		$id: 'expense',
		additionalProperties: false,
	},
);

export const ExpenseResponseSchema = Type.Object(
	{
		...ExpenseSchema.properties,
		id: Type.String(),
		farmId: Type.String(),
		speciesId: Type.Optional(Type.String()),
		breedId: Type.Optional(Type.String()),
		animalId: Type.Optional(Type.String()),
		lotId: Type.Optional(Type.String()),
		createdBy: Type.String(),
	},
	{
		$id: 'expenseResponse',
		additionalProperties: false,
	},
);

export const ExpenseCreateSchema = Type.Object(
	{
		date: Type.String(),
		amount: Type.Number({ minimum: 0 }),
		description: Type.Optional(Type.String()),
		category: Type.Enum(ExpenseCategory),
		speciesId: Type.Optional(Type.String()),
		breedId: Type.Optional(Type.String()),
		animalId: Type.Optional(Type.String()),
		lotId: Type.Optional(Type.String()),
		vendor: Type.Optional(Type.String()),
		paymentMethod: Type.Optional(Type.Enum(PaymentMethod)),
		invoiceNumber: Type.Optional(Type.String()),
		quantity: Type.Optional(Type.Number({ minimum: 0 })),
		quantityUnit: Type.Optional(Type.Enum(QuantityUnit)),
		unitCost: Type.Optional(Type.Number({ minimum: 0 })),
		status: Type.Optional(Type.Enum(ExpenseStatus)),
	},
	{
		$id: 'expenseCreate',
		additionalProperties: false,
	},
);

export const ExpenseUpdateSchema = Type.Object(
	{
		date: Type.Optional(Type.String()),
		amount: Type.Optional(Type.Number({ minimum: 0 })),
		description: Type.Optional(Type.String()),
		category: Type.Optional(Type.Enum(ExpenseCategory)),
		speciesId: Type.Optional(Type.String()),
		breedId: Type.Optional(Type.String()),
		animalId: Type.Optional(Type.String()),
		lotId: Type.Optional(Type.String()),
		vendor: Type.Optional(Type.String()),
		paymentMethod: Type.Optional(Type.Enum(PaymentMethod)),
		invoiceNumber: Type.Optional(Type.String()),
		quantity: Type.Optional(Type.Number({ minimum: 0 })),
		quantityUnit: Type.Optional(Type.Enum(QuantityUnit)),
		unitCost: Type.Optional(Type.Number({ minimum: 0 })),
		status: Type.Optional(Type.Enum(ExpenseStatus)),
	},
	{
		$id: 'expenseUpdate',
		additionalProperties: false,
	},
);

const ExpenseQuerySchema = Type.Object(
	{
		category: Type.Optional(Type.Enum(ExpenseCategory)),
		paymentMethod: Type.Optional(Type.Enum(PaymentMethod)),
		status: Type.Optional(Type.Enum(ExpenseStatus)),
	},
	{
		$id: 'expenseQuery',
		additionalProperties: false,
	},
);

const ExpenseParamsSchema = Type.Object({
	id: Type.String(),
});

export type Expense = Static<typeof ExpenseSchema>;
export type ExpenseResponse = Static<typeof ExpenseResponseSchema>;
export type ExpenseCreate = Static<typeof ExpenseCreateSchema>;
export type ExpenseUpdate = Static<typeof ExpenseUpdateSchema>;
export type ExpenseQuery = Static<typeof ExpenseQuerySchema>;
export type ExpenseParams = Static<typeof ExpenseParamsSchema>;

export const listExpensesSchema = createGetEndpointSchema({
	querystring: ExpenseQuerySchema,
	dataSchema: Type.Array(ExpenseResponseSchema),
	errorCodes: [404],
});

export const getExpenseSchema = createGetEndpointSchema({
	params: ExpenseParamsSchema,
	dataSchema: ExpenseResponseSchema,
	errorCodes: [404],
});

export const createExpenseSchema = createPostEndpointSchema({
	body: ExpenseCreateSchema,
	dataSchema: ExpenseResponseSchema,
	errorCodes: [400, 404],
});

export const updateExpenseSchema = createUpdateEndpointSchema({
	params: ExpenseParamsSchema,
	body: ExpenseUpdateSchema,
	dataSchema: ExpenseResponseSchema,
	errorCodes: [400, 404],
});

export const deleteExpenseSchema = createDeleteEndpointSchema({
	params: ExpenseParamsSchema,
	errorCodes: [404],
});
