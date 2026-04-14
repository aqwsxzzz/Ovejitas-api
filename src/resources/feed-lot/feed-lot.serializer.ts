import { encodeId } from '../../utils/id-hash-util';
import { FeedLotModel } from './feed-lot.model';
import { FeedLotResponse } from './feed-lot.schema';

export class FeedLotSerializer {
	static serialize(lot: FeedLotModel): FeedLotResponse {
		return {
			id: encodeId(lot.id),
			farmId: encodeId(lot.farmId),
			feedTypeId: encodeId(lot.feedTypeId),
			qtyPurchased: Number(lot.qtyPurchased),
			qtyRemaining: Number(lot.qtyRemaining),
			unitPrice: Number(lot.unitPrice),
			purchasedAt: lot.purchasedAt,
			supplier: lot.supplier,
			notes: lot.notes,
			createdBy: encodeId(lot.createdBy),
			createdAt: lot.createdAt,
			updatedAt: lot.updatedAt,
		};
	}

	static serializeMany(lots: FeedLotModel[]): FeedLotResponse[] {
		return lots.map(l => this.serialize(l));
	}
}
