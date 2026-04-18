import { encodeId } from '../../utils/id-hash-util';
import { EggPricingModel } from './egg-pricing.model';
import { EggPricingResponse } from './egg-pricing.schema';

export class EggPricingSerializer {
	static serialize(pricing: EggPricingModel, currency: string | null): EggPricingResponse {
		return {
			id: encodeId(pricing.id),
			farmId: encodeId(pricing.farmId),
			pricePerEgg: Number(pricing.pricePerEgg),
			currency,
			effectiveFrom: pricing.effectiveFrom,
			effectiveTo: pricing.effectiveTo,
			createdAt: pricing.createdAt,
			updatedAt: pricing.updatedAt,
		};
	}

	static serializeMany(rows: EggPricingModel[], currency: string | null): EggPricingResponse[] {
		return rows.map(r => this.serialize(r, currency));
	}
}
