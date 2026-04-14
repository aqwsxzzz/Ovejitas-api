import { Op, QueryTypes } from 'sequelize';
import { BaseService } from '../../services/base.service';
import { encodeId } from '../../utils/id-hash-util';
import { CostByFlockResponse, CostByLotResponse } from './feed-report.schema';

interface CostByFlockRow {
	flock_id: number | null;
	feed_type_id: number;
	total_qty: string;
	total_cost: string;
}

interface CostByLotRow {
	flock_id: number | null;
	total_qty: string;
	total_cost: string;
}

export class FeedReportService extends BaseService {
	async getCostByFlock(
		farmId: number,
		filters: { from?: string; to?: string; flockId?: number },
	): Promise<CostByFlockResponse> {
		const conditions: string[] = ['fc.farm_id = :farmId'];
		const replacements: Record<string, unknown> = { farmId };

		if (filters.from) {
			conditions.push('fc.consumed_at >= :from');
			replacements.from = filters.from;
		}
		if (filters.to) {
			conditions.push('fc.consumed_at <= :to');
			replacements.to = filters.to;
		}
		if (filters.flockId !== undefined) {
			conditions.push('fc.flock_id = :flockId');
			replacements.flockId = filters.flockId;
		}

		const rows = await this.db.sequelize.query<CostByFlockRow>(
			`SELECT
				fc.flock_id,
				fc.feed_type_id,
				SUM(fcl.qty_drawn) AS total_qty,
				SUM(fcl.qty_drawn * fcl.unit_price_snapshot) AS total_cost
			 FROM feed_consumptions fc
			 INNER JOIN feed_consumption_lots fcl ON fcl.consumption_id = fc.id
			 WHERE ${conditions.join(' AND ')}
			 GROUP BY fc.flock_id, fc.feed_type_id
			 ORDER BY fc.flock_id NULLS LAST, fc.feed_type_id`,
			{ replacements, type: QueryTypes.SELECT },
		);

		return this.buildCostByFlockResponse(rows, filters.from ?? null, filters.to ?? null);
	}

	async getCostByLot(farmId: number, lotId: number): Promise<CostByLotResponse | null> {
		const lot = await this.db.models.FeedLot.findOne({ where: { id: lotId, farmId } });
		if (!lot) return null;

		const rows = await this.db.sequelize.query<CostByLotRow>(
			`SELECT
				fc.flock_id,
				SUM(fcl.qty_drawn) AS total_qty,
				SUM(fcl.qty_drawn * fcl.unit_price_snapshot) AS total_cost
			 FROM feed_consumption_lots fcl
			 INNER JOIN feed_consumptions fc ON fc.id = fcl.consumption_id
			 WHERE fcl.lot_id = :lotId
			 GROUP BY fc.flock_id
			 ORDER BY fc.flock_id NULLS LAST`,
			{ replacements: { lotId }, type: QueryTypes.SELECT },
		);

		const qtyPurchased = Number(lot.qtyPurchased);
		const qtyRemaining = Number(lot.qtyRemaining);
		const qtyDrawn = Number((qtyPurchased - qtyRemaining).toFixed(3));
		const totalCost = Number((qtyDrawn * Number(lot.unitPrice)).toFixed(2));

		return {
			lotId: encodeId(lot.id),
			feedTypeId: encodeId(lot.feedTypeId),
			qtyPurchased,
			qtyRemaining,
			qtyDrawn,
			totalCost,
			byFlock: rows.map(row => ({
				flockId: row.flock_id != null ? encodeId(row.flock_id) : null,
				totalQty: Number(row.total_qty),
				totalCost: Number(Number(row.total_cost).toFixed(2)),
			})),
		};
	}

	private buildCostByFlockResponse(
		rows: CostByFlockRow[],
		from: string | null,
		to: string | null,
	): CostByFlockResponse {
		const byFlock = new Map<number | null, {
			totalQty: number;
			totalCost: number;
			feedTypes: Map<number, { totalQty: number; totalCost: number }>;
		}>();

		for (const row of rows) {
			const qty = Number(row.total_qty);
			const cost = Number(row.total_cost);
			const flockEntry = byFlock.get(row.flock_id) ?? {
				totalQty: 0,
				totalCost: 0,
				feedTypes: new Map(),
			};
			flockEntry.totalQty += qty;
			flockEntry.totalCost += cost;
			flockEntry.feedTypes.set(row.feed_type_id, { totalQty: qty, totalCost: cost });
			byFlock.set(row.flock_id, flockEntry);
		}

		return {
			from,
			to,
			flocks: Array.from(byFlock.entries()).map(([flockId, entry]) => ({
				flockId: flockId != null ? encodeId(flockId) : null,
				totalQty: Number(entry.totalQty.toFixed(3)),
				totalCost: Number(entry.totalCost.toFixed(2)),
				byFeedType: Array.from(entry.feedTypes.entries()).map(([feedTypeId, ft]) => ({
					feedTypeId: encodeId(feedTypeId),
					totalQty: Number(ft.totalQty.toFixed(3)),
					totalCost: Number(ft.totalCost.toFixed(2)),
				})),
			})),
		};
	}
}
