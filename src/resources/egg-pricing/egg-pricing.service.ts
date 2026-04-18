import { Op, Transaction } from 'sequelize';
import { BaseService } from '../../services/base.service';
import { EggPricingModel } from './egg-pricing.model';

export class EggPricingService extends BaseService {
	async getActive(farmId: number, onDate: string = todayISO()): Promise<EggPricingModel | null> {
		return this.db.models.EggPricing.findOne({
			where: {
				farmId,
				effectiveFrom: { [Op.lte]: onDate },
				[Op.or]: [
					{ effectiveTo: null },
					{ effectiveTo: { [Op.gte]: onDate } },
				],
			},
			order: [['effective_from', 'DESC']],
		});
	}

	async getHistory(farmId: number): Promise<EggPricingModel[]> {
		return this.db.models.EggPricing.findAll({
			where: { farmId },
			order: [['effective_from', 'DESC']],
		});
	}

	async setPrice(farmId: number, pricePerEgg: number, effectiveFrom: string): Promise<EggPricingModel> {
		return this.db.sequelize.transaction(async (transaction) => {
			await this.closeOpenPricing(farmId, effectiveFrom, transaction);
			return this.db.models.EggPricing.create({
				farmId,
				pricePerEgg,
				effectiveFrom,
				effectiveTo: null,
			}, { transaction });
		});
	}

	private async closeOpenPricing(farmId: number, newEffectiveFrom: string, transaction: Transaction): Promise<void> {
		const current = await this.db.models.EggPricing.findOne({
			where: { farmId, effectiveTo: null },
			transaction,
			lock: true,
		});

		if (!current) return;

		if (current.effectiveFrom >= newEffectiveFrom) {
			throw new EggPricingOrderingError(
				`New pricing effectiveFrom (${newEffectiveFrom}) must be after current pricing effectiveFrom (${current.effectiveFrom}).`,
			);
		}

		const priorDay = shiftDateByDays(newEffectiveFrom, -1);
		await current.update({ effectiveTo: priorDay }, { transaction });
	}
}

export class EggPricingOrderingError extends Error {
	constructor(message: string) {
		super(message);
		this.name = 'EggPricingOrderingError';
	}
}

function todayISO(): string {
	return new Date().toISOString().slice(0, 10);
}

function shiftDateByDays(isoDate: string, days: number): string {
	const d = new Date(`${isoDate}T00:00:00Z`);
	d.setUTCDate(d.getUTCDate() + days);
	return d.toISOString().slice(0, 10);
}
