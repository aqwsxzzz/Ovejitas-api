import { describe, it, expect } from 'vitest';
import { ExpenseSerializer } from '../../src/resources/expense/expense.serializer';
import { encodeId } from '../../src/utils/id-hash-util';
import { ExpenseModel } from '../../src/resources/expense/expense.model';

function makeExpense(overrides?: Partial<ExpenseModel>): ExpenseModel {
	return {
		id: 1,
		farmId: 10,
		date: '2025-06-15',
		amount: 250.50,
		description: 'Feed purchase',
		category: 'feed',
		speciesId: null,
		breedId: null,
		animalId: null,
		lotId: null,
		vendor: 'Farm Supply Co',
		paymentMethod: 'cash',
		invoiceNumber: 'INV-001',
		quantity: 5,
		quantityUnit: 'bags',
		unitCost: 50.10,
		status: 'paid',
		createdBy: 100,
		createdAt: '2025-01-01T00:00:00.000Z',
		updatedAt: '2025-01-01T00:00:00.000Z',
		...overrides,
	} as ExpenseModel;
}

describe('ExpenseSerializer', () => {
	describe('serialize', () => {
		it('encodes id, farmId, and createdBy', () => {
			const expense = makeExpense({ id: 1, farmId: 10, createdBy: 100 });
			const result = ExpenseSerializer.serialize(expense);
			expect(result.id).toBe(encodeId(1));
			expect(result.farmId).toBe(encodeId(10));
			expect(result.createdBy).toBe(encodeId(100));
		});

		it('encodes optional relation ids when present', () => {
			const expense = makeExpense({ speciesId: 20, breedId: 30, animalId: 40 });
			const result = ExpenseSerializer.serialize(expense);
			expect(result.speciesId).toBe(encodeId(20));
			expect(result.breedId).toBe(encodeId(30));
			expect(result.animalId).toBe(encodeId(40));
		});

		it('returns undefined for optional relation ids when null', () => {
			const expense = makeExpense({ speciesId: null, breedId: null, animalId: null });
			const result = ExpenseSerializer.serialize(expense);
			expect(result.speciesId).toBeUndefined();
			expect(result.breedId).toBeUndefined();
			expect(result.animalId).toBeUndefined();
		});

		it('includes scalar fields', () => {
			const expense = makeExpense({ amount: 99.99, category: 'veterinary', date: '2025-03-01' });
			const result = ExpenseSerializer.serialize(expense);
			expect(result.amount).toBe(99.99);
			expect(result.category).toBe('veterinary');
			expect(result.date).toBe('2025-03-01');
		});

		it('handles null optional fields with defaults', () => {
			const expense = makeExpense({
				description: null,
				vendor: null,
				invoiceNumber: null,
				quantity: null,
				unitCost: null,
			});
			const result = ExpenseSerializer.serialize(expense);
			expect(result.description).toBe('');
			expect(result.vendor).toBe('');
			expect(result.invoiceNumber).toBe('');
			expect(result.quantity).toBe(0);
			expect(result.unitCost).toBe(0);
		});

		it('handles null enum fields', () => {
			const expense = makeExpense({
				paymentMethod: null,
				quantityUnit: null,
				status: null,
			});
			const result = ExpenseSerializer.serialize(expense);
			expect(result.paymentMethod).toBeUndefined();
			expect(result.quantityUnit).toBeUndefined();
			expect(result.status).toBeUndefined();
		});
	});

	describe('serializeMany', () => {
		it('serializes an array of expenses', () => {
			const expenses = [makeExpense({ id: 1 }), makeExpense({ id: 2 })];
			const result = ExpenseSerializer.serializeMany(expenses);
			expect(result).toHaveLength(2);
			expect(result[0].id).toBe(encodeId(1));
			expect(result[1].id).toBe(encodeId(2));
		});
	});
});
