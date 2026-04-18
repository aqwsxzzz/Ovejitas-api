import { QueryTypes } from 'sequelize';
import { BaseService } from '../../services/base.service';
import { Database } from '../../database';
import { encodeId } from '../../utils/id-hash-util';
import { BucketedFeedCostRow, BucketPeriod, FeedReportService } from '../feed-report/feed-report.service';
import { FlockProfitabilityResponse } from './flock-profitability.schema';
import {
	addRow,
	buildBreakdown,
	buildSummary,
	emptyRow,
	RawRow,
} from './flock-profitability.metrics';

const REVENUE_BUCKET: Record<BucketPeriod, string> = {
	daily: "to_char(ec.date, 'YYYY-MM-DD')",
	weekly: `to_char(date_trunc('week', ec.date), 'IYYY-"W"IW')`,
	monthly: "to_char(ec.date, 'YYYY-MM')",
};

interface RevenueRow {
	flock_id: number;
	flock_name: string;
	species_id: number;
	period: string;
	total_eggs: string;
	sellable_eggs: string;
	broken_eggs: string;
	revenue: string;
	uncovered_count: string;
}

export interface ProfitabilityInput {
	farmId: number;
	period: BucketPeriod;
	from: string;
	to: string;
	flockId?: number;
}

interface FlockMeta { name: string; speciesId: number }

export class EggPricingMissingError extends Error {
	constructor() {
		super('Egg pricing not configured for this farm');
		this.name = 'EggPricingMissingError';
	}
}

export class FlockProfitabilityService extends BaseService {
	private readonly feedReport: FeedReportService;

	constructor(db: Database, feedReport: FeedReportService) {
		super(db);
		this.feedReport = feedReport;
	}

	async getReport(input: ProfitabilityInput): Promise<FlockProfitabilityResponse> {
		const [pricingCount, revenueRows, feedRows, currency] = await Promise.all([
			this.countPricing(input.farmId),
			this.queryRevenue(input),
			this.feedReport.getCostByFlockBucketed(input.farmId, input),
			this.getFarmCurrency(input.farmId),
		]);

		if (pricingCount === 0) throw new EggPricingMissingError();

		const meta = collectMetaFromRevenue(revenueRows);
		const grid = buildGrid(revenueRows, feedRows);
		await this.hydrateMissingMeta(input.farmId, grid, meta);

		return {
			farmId: encodeId(input.farmId),
			currency,
			reportPeriod: input.period,
			dateRange: { from: input.from, to: input.to },
			flocks: buildFlockRows(grid, meta, revenueRows),
		};
	}

	private async countPricing(farmId: number): Promise<number> {
		return this.db.models.EggPricing.count({ where: { farmId } });
	}

	private async getFarmCurrency(farmId: number): Promise<string | null> {
		const farm = await this.db.models.Farm.findByPk(farmId, { attributes: ['currency'] });
		return farm?.dataValues.currency ?? null;
	}

	private async queryRevenue(input: ProfitabilityInput): Promise<RevenueRow[]> {
		const conditions: string[] = [
			'f.farm_id = :farmId',
			'ec.date >= :from',
			'ec.date <= :to',
		];
		const replacements: Record<string, unknown> = {
			farmId: input.farmId,
			from: input.from,
			to: input.to,
		};
		if (input.flockId !== undefined) {
			conditions.push('ec.flock_id = :flockId');
			replacements.flockId = input.flockId;
		}

		return this.db.sequelize.query<RevenueRow>(
			`SELECT
				ec.flock_id,
				f.name AS flock_name,
				f.species_id,
				${REVENUE_BUCKET[input.period]} AS period,
				SUM(ec.total_eggs) AS total_eggs,
				SUM(ec.total_eggs - ec.broken_eggs) AS sellable_eggs,
				SUM(ec.broken_eggs) AS broken_eggs,
				SUM((ec.total_eggs - ec.broken_eggs) * COALESCE(ep.price_per_egg, 0)) AS revenue,
				COUNT(*) FILTER (WHERE ep.id IS NULL) AS uncovered_count
			 FROM egg_collections ec
			 INNER JOIN flocks f ON f.id = ec.flock_id
			 LEFT JOIN egg_pricings ep
				ON ep.farm_id = f.farm_id
				AND ec.date >= ep.effective_from
				AND (ep.effective_to IS NULL OR ec.date <= ep.effective_to)
			 WHERE ${conditions.join(' AND ')}
			 GROUP BY ec.flock_id, f.name, f.species_id, period
			 ORDER BY ec.flock_id, period`,
			{ replacements, type: QueryTypes.SELECT },
		);
	}

	private async hydrateMissingMeta(
		farmId: number,
		grid: Map<number, Map<string, RawRow>>,
		meta: Map<number, FlockMeta>,
	): Promise<void> {
		const missing = Array.from(grid.keys()).filter(id => !meta.has(id));
		if (missing.length === 0) return;
		const rows = await this.db.models.Flock.findAll({
			where: { id: missing, farmId },
			attributes: ['id', 'name', 'speciesId'],
		});
		for (const row of rows) {
			meta.set(row.id, { name: row.name, speciesId: row.speciesId });
		}
	}
}

function collectMetaFromRevenue(revenue: RevenueRow[]): Map<number, FlockMeta> {
	const meta = new Map<number, FlockMeta>();
	for (const r of revenue) {
		if (!meta.has(r.flock_id)) {
			meta.set(r.flock_id, { name: r.flock_name, speciesId: r.species_id });
		}
	}
	return meta;
}

function buildGrid(revenue: RevenueRow[], feed: BucketedFeedCostRow[]): Map<number, Map<string, RawRow>> {
	const grid = new Map<number, Map<string, RawRow>>();

	for (const r of revenue) {
		upsertCell(grid, r.flock_id, r.period, {
			eggsCollected: Number(r.total_eggs),
			eggsSellable: Number(r.sellable_eggs),
			brokenEggs: Number(r.broken_eggs),
			eggRevenue: Number(r.revenue),
			feedQuantity: 0,
			feedCost: 0,
		});
	}
	for (const f of feed) {
		upsertCell(grid, f.flockId, f.period, {
			eggsCollected: 0,
			eggsSellable: 0,
			brokenEggs: 0,
			eggRevenue: 0,
			feedQuantity: f.totalQty,
			feedCost: f.totalCost,
		});
	}
	return grid;
}

function upsertCell(
	grid: Map<number, Map<string, RawRow>>,
	flockId: number,
	period: string,
	row: RawRow,
): void {
	const bucket = grid.get(flockId) ?? new Map<string, RawRow>();
	bucket.set(period, addRow(bucket.get(period) ?? emptyRow(), row));
	grid.set(flockId, bucket);
}

function buildFlockRows(
	grid: Map<number, Map<string, RawRow>>,
	meta: Map<number, FlockMeta>,
	revenue: RevenueRow[],
): FlockProfitabilityResponse['flocks'] {
	const uncoveredByFlock = new Map<number, number>();
	for (const r of revenue) {
		uncoveredByFlock.set(
			r.flock_id,
			(uncoveredByFlock.get(r.flock_id) ?? 0) + Number(r.uncovered_count),
		);
	}

	const flocks: FlockProfitabilityResponse['flocks'] = [];
	const sortedFlockIds = Array.from(grid.keys()).sort((a, b) => a - b);

	for (const flockId of sortedFlockIds) {
		const periods = grid.get(flockId);
		const metaRow = meta.get(flockId);
		if (!periods || !metaRow) continue;

		let total = emptyRow();
		const periodBreakdown = Array.from(periods.entries())
			.sort(([a], [b]) => a.localeCompare(b))
			.map(([period, row]) => {
				total = addRow(total, row);
				return { period, ...buildBreakdown(row) };
			});

		const warnings: string[] = [];
		const uncovered = uncoveredByFlock.get(flockId) ?? 0;
		if (uncovered > 0) {
			warnings.push(`${uncovered} egg collection(s) had no active pricing rule and were priced at 0.`);
		}

		flocks.push({
			flockId: encodeId(flockId),
			flockName: metaRow.name,
			speciesId: encodeId(metaRow.speciesId),
			...buildSummary(total),
			warnings,
			periodBreakdown,
		});
	}

	return flocks;
}
