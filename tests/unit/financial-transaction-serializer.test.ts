import { describe, it, expect } from 'vitest';
import { FinancialTransactionSerializer } from '../../src/resources/financial-transaction/financial-transaction.serializer';
import { encodeId } from '../../src/utils/id-hash-util';
import { FinancialTransactionModel } from '../../src/resources/financial-transaction/financial-transaction.model';

function makeTransaction(overrides?: Partial<FinancialTransactionModel>): FinancialTransactionModel {
	return {
		id: 1,
		farmId: 10,
		type: 'expense',
		amount: 150.50,
		description: 'Feed purchase',
		speciesId: 20,
		date: '2026-03-15',
		createdBy: 5,
		createdAt: '2026-03-15T00:00:00.000Z',
		updatedAt: '2026-03-15T00:00:00.000Z',
		...overrides,
	} as FinancialTransactionModel;
}

describe('FinancialTransactionSerializer', () => {
	describe('serialize', () => {
		it('encodes all id fields as hashes', () => {
			const transaction = makeTransaction({ id: 1, farmId: 10, speciesId: 20, createdBy: 5 });
			const result = FinancialTransactionSerializer.serialize(transaction);
			expect(result.id).toBe(encodeId(1));
			expect(result.farmId).toBe(encodeId(10));
			expect(result.speciesId).toBe(encodeId(20));
			expect(result.createdBy).toBe(encodeId(5));
		});

		it('includes type field correctly for expense', () => {
			const transaction = makeTransaction({ type: 'expense' });
			const result = FinancialTransactionSerializer.serialize(transaction);
			expect(result.type).toBe('expense');
		});

		it('includes type field correctly for income', () => {
			const transaction = makeTransaction({ type: 'income' });
			const result = FinancialTransactionSerializer.serialize(transaction);
			expect(result.type).toBe('income');
		});

		it('converts amount to number', () => {
			const transaction = makeTransaction({ amount: '250.75' as unknown as number });
			const result = FinancialTransactionSerializer.serialize(transaction);
			expect(result.amount).toBe(250.75);
			expect(typeof result.amount).toBe('number');
		});

		it('includes scalar fields directly', () => {
			const transaction = makeTransaction({
				description: 'Vet visit',
				date: '2026-02-20',
			});
			const result = FinancialTransactionSerializer.serialize(transaction);
			expect(result.description).toBe('Vet visit');
			expect(result.date).toBe('2026-02-20');
		});

		it('preserves null description', () => {
			const transaction = makeTransaction({ description: null });
			const result = FinancialTransactionSerializer.serialize(transaction);
			expect(result.description).toBeNull();
		});

		it('includes timestamp fields', () => {
			const transaction = makeTransaction({
				createdAt: '2026-03-15T10:00:00.000Z',
				updatedAt: '2026-03-15T12:00:00.000Z',
			});
			const result = FinancialTransactionSerializer.serialize(transaction);
			expect(result.createdAt).toBe('2026-03-15T10:00:00.000Z');
			expect(result.updatedAt).toBe('2026-03-15T12:00:00.000Z');
		});
	});

	describe('serializeMany', () => {
		it('serializes an array of transactions', () => {
			const transactions = [makeTransaction({ id: 1 }), makeTransaction({ id: 2 })];
			const result = FinancialTransactionSerializer.serializeMany(transactions);
			expect(result).toHaveLength(2);
			expect(result[0]!.id).toBe(encodeId(1));
			expect(result[1]!.id).toBe(encodeId(2));
		});

		it('returns empty array for empty input', () => {
			const result = FinancialTransactionSerializer.serializeMany([]);
			expect(result).toHaveLength(0);
		});
	});
});
