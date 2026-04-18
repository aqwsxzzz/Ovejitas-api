import { describe, it, expect } from 'vitest';
import {
	addRow,
	buildBreakdown,
	buildSummary,
	emptyRow,
	RawRow,
} from '../../src/resources/flock-profitability/flock-profitability.metrics';

function row(overrides: Partial<RawRow>): RawRow {
	return { ...emptyRow(), ...overrides };
}

describe('flock-profitability metrics', () => {
	describe('buildSummary', () => {
		it('computes profit, margin, costPerDozen and fcr for a revenue+cost row', () => {
			const summary = buildSummary(row({
				eggsCollected: 300,
				eggsSellable: 288,
				brokenEggs: 12,
				eggRevenue: 144,
				feedQuantity: 60,
				feedCost: 90,
			}));

			expect(summary.totalEggRevenue).toBe(144);
			expect(summary.totalFeedCost).toBe(90);
			expect(summary.profit).toBe(54);
			expect(summary.profitMargin).toBe(37.5);
			expect(summary.eggsCollectedStacks).toBe(10);
			expect(summary.costPerDozenEggs).toBe(3.75);
			expect(summary.fcrKgPerDozen).toBe(2.5);
		});

		it('returns negative profit when feed cost exceeds revenue', () => {
			const summary = buildSummary(row({
				eggsCollected: 30,
				eggsSellable: 30,
				eggRevenue: 10,
				feedQuantity: 5,
				feedCost: 40,
			}));

			expect(summary.profit).toBe(-30);
			expect(summary.profitMargin).toBe(-300);
		});

		it('returns null margin and null KPIs when there are no sellable eggs', () => {
			const summary = buildSummary(row({
				eggsCollected: 5,
				eggsSellable: 0,
				brokenEggs: 5,
				feedQuantity: 3,
				feedCost: 12,
			}));

			expect(summary.profitMargin).toBeNull();
			expect(summary.costPerDozenEggs).toBeNull();
			expect(summary.fcrKgPerDozen).toBeNull();
			expect(summary.profit).toBe(-12);
		});
	});

	describe('buildBreakdown', () => {
		it('mirrors summary math at the period level', () => {
			const breakdown = buildBreakdown(row({
				eggsCollected: 60,
				eggsSellable: 60,
				eggRevenue: 30,
				feedQuantity: 10,
				feedCost: 15,
			}));

			expect(breakdown.profit).toBe(15);
			expect(breakdown.profitMargin).toBe(50);
		});
	});

	describe('addRow', () => {
		it('sums every numeric field', () => {
			const a = row({ eggsCollected: 10, eggRevenue: 5, feedCost: 3 });
			const b = row({ eggsCollected: 4, eggRevenue: 2, feedCost: 1 });
			expect(addRow(a, b)).toEqual(row({
				eggsCollected: 14,
				eggRevenue: 7,
				feedCost: 4,
			}));
		});
	});
});
