import { encodeId } from '../../utils/id-hash-util';
import { FeedConsumptionResponse } from './feed-consumption.schema';
import { FeedConsumptionWithLots } from './feed-consumption.service';

export class FeedConsumptionSerializer {
	static serialize(consumption: FeedConsumptionWithLots): FeedConsumptionResponse {
		const lots = consumption.lots ?? [];
		const totalCost = lots.reduce(
			(sum, lot) => sum + Number(lot.qtyDrawn) * Number(lot.unitPriceSnapshot),
			0,
		);

		return {
			id: encodeId(consumption.id),
			farmId: encodeId(consumption.farmId),
			flockId: consumption.flockId !== null ? encodeId(consumption.flockId) : null,
			feedTypeId: encodeId(consumption.feedTypeId),
			consumedAt: consumption.consumedAt,
			qty: Number(consumption.qty),
			reason: consumption.reason,
			notes: consumption.notes,
			createdBy: encodeId(consumption.createdBy),
			totalCost: Number(totalCost.toFixed(2)),
			lots: lots.map(lot => ({
				id: encodeId(lot.id),
				lotId: encodeId(lot.lotId),
				qtyDrawn: Number(lot.qtyDrawn),
				unitPriceSnapshot: Number(lot.unitPriceSnapshot),
			})),
			createdAt: consumption.createdAt,
			updatedAt: consumption.updatedAt,
		};
	}

	static serializeMany(consumptions: FeedConsumptionWithLots[]): FeedConsumptionResponse[] {
		return consumptions.map(c => this.serialize(c));
	}
}
