const DOZEN = 12;
const STACK = 30;
const ROUND_MONEY = 2;
const ROUND_QTY = 3;
const ROUND_RATIO = 4;

export interface RawRow {
	eggsCollected: number;
	eggsSellable: number;
	brokenEggs: number;
	eggRevenue: number;
	feedQuantity: number;
	feedCost: number;
}

export interface MetricsSummary {
	eggsCollected: number;
	eggsSellable: number;
	brokenEggs: number;
	eggsCollectedStacks: number;
	totalEggRevenue: number;
	feedQuantity: number;
	totalFeedCost: number;
	totalExpenses: number;
	profit: number;
	profitMargin: number | null;
	costPerDozenEggs: number | null;
	fcrKgPerDozen: number | null;
}

export interface BreakdownMetrics {
	eggsCollected: number;
	eggsSellable: number;
	brokenEggs: number;
	eggRevenue: number;
	feedQuantity: number;
	feedCost: number;
	profit: number;
	profitMargin: number | null;
}

export function buildSummary(row: RawRow): MetricsSummary {
	const totalExpenses = row.feedCost;
	const profit = row.eggRevenue - totalExpenses;
	const profitMargin = row.eggRevenue > 0
		? round((profit / row.eggRevenue) * 100, ROUND_RATIO)
		: null;
	const costPerDozenEggs = row.eggsSellable > 0
		? round((row.feedCost * DOZEN) / row.eggsSellable, ROUND_MONEY)
		: null;
	const fcrKgPerDozen = row.eggsSellable > 0
		? round((row.feedQuantity * DOZEN) / row.eggsSellable, ROUND_RATIO)
		: null;

	return {
		eggsCollected: row.eggsCollected,
		eggsSellable: row.eggsSellable,
		brokenEggs: row.brokenEggs,
		eggsCollectedStacks: round(row.eggsCollected / STACK, ROUND_RATIO),
		totalEggRevenue: round(row.eggRevenue, ROUND_MONEY),
		feedQuantity: round(row.feedQuantity, ROUND_QTY),
		totalFeedCost: round(row.feedCost, ROUND_MONEY),
		totalExpenses: round(totalExpenses, ROUND_MONEY),
		profit: round(profit, ROUND_MONEY),
		profitMargin,
		costPerDozenEggs,
		fcrKgPerDozen,
	};
}

export function buildBreakdown(row: RawRow): BreakdownMetrics {
	const profit = row.eggRevenue - row.feedCost;
	const profitMargin = row.eggRevenue > 0
		? round((profit / row.eggRevenue) * 100, ROUND_RATIO)
		: null;
	return {
		eggsCollected: row.eggsCollected,
		eggsSellable: row.eggsSellable,
		brokenEggs: row.brokenEggs,
		eggRevenue: round(row.eggRevenue, ROUND_MONEY),
		feedQuantity: round(row.feedQuantity, ROUND_QTY),
		feedCost: round(row.feedCost, ROUND_MONEY),
		profit: round(profit, ROUND_MONEY),
		profitMargin,
	};
}

export function emptyRow(): RawRow {
	return {
		eggsCollected: 0,
		eggsSellable: 0,
		brokenEggs: 0,
		eggRevenue: 0,
		feedQuantity: 0,
		feedCost: 0,
	};
}

export function addRow(a: RawRow, b: RawRow): RawRow {
	return {
		eggsCollected: a.eggsCollected + b.eggsCollected,
		eggsSellable: a.eggsSellable + b.eggsSellable,
		brokenEggs: a.brokenEggs + b.brokenEggs,
		eggRevenue: a.eggRevenue + b.eggRevenue,
		feedQuantity: a.feedQuantity + b.feedQuantity,
		feedCost: a.feedCost + b.feedCost,
	};
}

function round(value: number, decimals: number): number {
	const factor = 10 ** decimals;
	return Math.round(value * factor) / factor;
}
