import { describe, it, expect } from 'vitest';
import { computeDraws, InsufficientStockError, DrainableLot } from '../../src/resources/feed-consumption/feed-consumption-fifo';

function lot(id: number, qtyRemaining: number, unitPrice: number): DrainableLot {
	return { id, qtyRemaining, unitPrice };
}

describe('computeDraws', () => {
	it('drains a single lot when capacity covers the request', () => {
		const lots = [lot(1, 10, 1)];

		const draws = computeDraws(lots, 8);

		expect(draws).toEqual([
			{ lotId: 1, qtyDrawn: 8, unitPriceSnapshot: 1 },
		]);
	});

	it('drains the oldest lot first when multiple lots have stock', () => {
		const lots = [lot(1, 10, 1), lot(2, 5, 2)];

		const draws = computeDraws(lots, 8);

		expect(draws).toEqual([
			{ lotId: 1, qtyDrawn: 8, unitPriceSnapshot: 1 },
		]);
	});

	it('spans across two lots when the first does not cover the request', () => {
		const lots = [lot(1, 10, 1), lot(2, 5, 2)];

		const draws = computeDraws(lots, 12);

		expect(draws).toEqual([
			{ lotId: 1, qtyDrawn: 10, unitPriceSnapshot: 1 },
			{ lotId: 2, qtyDrawn: 2, unitPriceSnapshot: 2 },
		]);
	});

	it('spans across three lots with mixed prices', () => {
		const lots = [lot(1, 3, 1), lot(2, 3, 2), lot(3, 3, 3)];

		const draws = computeDraws(lots, 7);

		expect(draws).toEqual([
			{ lotId: 1, qtyDrawn: 3, unitPriceSnapshot: 1 },
			{ lotId: 2, qtyDrawn: 3, unitPriceSnapshot: 2 },
			{ lotId: 3, qtyDrawn: 1, unitPriceSnapshot: 3 },
		]);
	});

	it('throws InsufficientStockError when total stock is less than requested', () => {
		const lots = [lot(1, 3, 1), lot(2, 1, 2)];

		expect(() => computeDraws(lots, 5)).toThrow(InsufficientStockError);
	});

	it('throws InsufficientStockError when no lots are available', () => {
		expect(() => computeDraws([], 1)).toThrow(InsufficientStockError);
	});

	it('attaches requested and available quantities to the error', () => {
		const lots = [lot(1, 2, 1)];

		try {
			computeDraws(lots, 5);
			expect.fail('Expected InsufficientStockError to be thrown');
		} catch (error) {
			expect(error).toBeInstanceOf(InsufficientStockError);
			expect((error as InsufficientStockError).requested).toBe(5);
			expect((error as InsufficientStockError).available).toBe(2);
		}
	});

	it('handles fractional kilogram quantities to 3 decimal places', () => {
		const lots = [lot(1, 1.5, 1.25), lot(2, 0.75, 2.5)];

		const draws = computeDraws(lots, 2);

		expect(draws).toEqual([
			{ lotId: 1, qtyDrawn: 1.5, unitPriceSnapshot: 1.25 },
			{ lotId: 2, qtyDrawn: 0.5, unitPriceSnapshot: 2.5 },
		]);
	});

	it('returns an empty draw list when requested qty is zero', () => {
		const lots = [lot(1, 10, 1)];

		const draws = computeDraws(lots, 0);

		expect(draws).toEqual([]);
	});
});
