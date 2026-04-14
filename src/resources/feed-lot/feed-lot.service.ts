import { FindOptions, Op } from 'sequelize';
import { BaseService } from '../../services/base.service';
import { FeedLotModel } from './feed-lot.model';
import { FeedLotCreate, FeedLotUpdate } from './feed-lot.schema';
import { PaginatedResult, PaginationParams } from '../../utils/pagination';
import { decodeId } from '../../utils/id-hash-util';

export class LotImmutableError extends Error {
	constructor(message: string) {
		super(message);
		this.name = 'LotImmutableError';
	}
}

export class FeedLotService extends BaseService {
	async getFeedLots(
		farmId: number,
		filters: { feedTypeId?: number; hasStock?: boolean },
		pagination: PaginationParams,
	): Promise<PaginatedResult<FeedLotModel>> {
		const where: Record<string, unknown> = { farmId };
		if (filters.feedTypeId !== undefined) {
			where.feedTypeId = filters.feedTypeId;
		}
		if (filters.hasStock) {
			where.qtyRemaining = { [Op.gt]: 0 };
		}

		const findOptions: FindOptions = {
			where,
			order: [['purchasedAt', 'DESC'], ['id', 'DESC']],
		};

		return this.findAllPaginated(this.db.models.FeedLot, findOptions, pagination);
	}

	async getFeedLotById(id: number, farmId: number): Promise<FeedLotModel | null> {
		return this.db.models.FeedLot.findOne({ where: { id, farmId } });
	}

	async createFeedLot(farmId: number, createdBy: number, data: FeedLotCreate): Promise<FeedLotModel> {
		const feedTypeId = decodeId(data.feedTypeId);
		if (!feedTypeId) {
			throw new Error('Invalid feed type ID');
		}

		return this.db.sequelize.transaction(async (transaction) => {
			const feedType = await this.db.models.FeedType.findOne({
				where: { id: feedTypeId, farmId },
				transaction,
			});
			if (!feedType) {
				throw new Error('Feed type not found');
			}

			return this.db.models.FeedLot.create({
				farmId,
				feedTypeId,
				qtyPurchased: data.qtyPurchased,
				qtyRemaining: data.qtyPurchased,
				unitPrice: data.unitPrice,
				purchasedAt: data.purchasedAt,
				supplier: data.supplier ?? null,
				notes: data.notes ?? null,
				createdBy,
			}, { transaction });
		});
	}

	async updateFeedLot(id: number, farmId: number, data: FeedLotUpdate): Promise<FeedLotModel | null> {
		return this.db.sequelize.transaction(async (transaction) => {
			const lot = await this.db.models.FeedLot.findOne({
				where: { id, farmId },
				transaction,
				lock: true,
			});

			if (!lot) {
				return null;
			}

			const isImmutable = Number(lot.qtyRemaining) !== Number(lot.qtyPurchased);
			const wantsPriceChange = data.unitPrice !== undefined && Number(data.unitPrice) !== Number(lot.unitPrice);
			const wantsDateChange = data.purchasedAt !== undefined && data.purchasedAt !== lot.purchasedAt;

			if (isImmutable && (wantsPriceChange || wantsDateChange)) {
				throw new LotImmutableError('Cannot edit price or purchase date after the lot has been partially consumed.');
			}

			const updates: Record<string, unknown> = {};
			if (data.unitPrice !== undefined) updates.unitPrice = data.unitPrice;
			if (data.purchasedAt !== undefined) updates.purchasedAt = data.purchasedAt;
			if (data.supplier !== undefined) updates.supplier = data.supplier;
			if (data.notes !== undefined) updates.notes = data.notes;

			await lot.update(updates, { transaction });
			return lot;
		});
	}

	async deleteFeedLot(id: number, farmId: number): Promise<boolean> {
		return this.db.sequelize.transaction(async (transaction) => {
			const lot = await this.db.models.FeedLot.findOne({
				where: { id, farmId },
				transaction,
			});

			if (!lot) {
				return false;
			}

			await lot.destroy({ transaction });
			return true;
		});
	}
}
