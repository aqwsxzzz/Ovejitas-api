import { Op, Transaction } from 'sequelize';
import { Database } from '../../database';

export class InsufficientStockError extends Error {
	constructor(public readonly requested: number, public readonly available: number) {
		super(`Insufficient stock: requested ${requested}, available ${available}`);
		this.name = 'InsufficientStockError';
	}
}

export interface DrainableLot {
	id: number;
	qtyRemaining: number;
	unitPrice: number;
}

export interface LotDraw {
	lotId: number;
	qtyDrawn: number;
	unitPriceSnapshot: number;
}

const DECIMAL_PLACES = 3;

function round(value: number): number {
	const factor = 10 ** DECIMAL_PLACES;
	return Math.round(value * factor) / factor;
}

export function computeDraws(lots: DrainableLot[], requestedQty: number): LotDraw[] {
	const draws: LotDraw[] = [];
	let remaining = round(requestedQty);

	for (const lot of lots) {
		if (remaining <= 0) break;
		const draw = round(Math.min(lot.qtyRemaining, remaining));
		if (draw <= 0) continue;
		draws.push({ lotId: lot.id, qtyDrawn: draw, unitPriceSnapshot: lot.unitPrice });
		remaining = round(remaining - draw);
	}

	if (remaining > 0) {
		const available = round(lots.reduce((sum, l) => sum + l.qtyRemaining, 0));
		throw new InsufficientStockError(requestedQty, available);
	}

	return draws;
}

export async function drainFIFO(
	db: Database,
	params: { farmId: number; feedTypeId: number; qty: number },
	transaction: Transaction,
): Promise<LotDraw[]> {
	const lots = await db.models.FeedLot.findAll({
		where: {
			farmId: params.farmId,
			feedTypeId: params.feedTypeId,
			qtyRemaining: { [Op.gt]: 0 },
		},
		// Consistent lock order (purchasedAt ASC, id ASC) prevents deadlocks
		// between concurrent consumptions on the same feed_type.
		order: [['purchasedAt', 'ASC'], ['id', 'ASC']],
		transaction,
		lock: transaction.LOCK.UPDATE,
	});

	const drainableLots: DrainableLot[] = lots.map(lot => ({
		id: lot.id,
		qtyRemaining: Number(lot.qtyRemaining),
		unitPrice: Number(lot.unitPrice),
	}));

	const draws = computeDraws(drainableLots, params.qty);

	for (const draw of draws) {
		await db.models.FeedLot.decrement('qtyRemaining', {
			by: draw.qtyDrawn,
			where: { id: draw.lotId },
			transaction,
		});
	}

	return draws;
}
