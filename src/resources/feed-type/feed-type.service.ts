import { FindOptions, Op } from 'sequelize';
import { BaseService } from '../../services/base.service';
import { FeedTypeModel } from './feed-type.model';
import { FeedTypeCreate, FeedTypeUpdate } from './feed-type.schema';
import { PaginatedResult, PaginationParams } from '../../utils/pagination';

export class FeedTypeService extends BaseService {
	async getFeedTypes(farmId: number, pagination: PaginationParams): Promise<PaginatedResult<FeedTypeModel>> {
		const findOptions: FindOptions = {
			where: { farmId },
			order: [['name', 'ASC']],
		};

		return this.findAllPaginated(this.db.models.FeedType, findOptions, pagination);
	}

	async getFeedTypeById(id: number, farmId: number): Promise<FeedTypeModel | null> {
		return this.db.models.FeedType.findOne({ where: { id, farmId } });
	}

	async createFeedType(farmId: number, data: FeedTypeCreate): Promise<FeedTypeModel> {
		return this.db.sequelize.transaction(async (transaction) => {
			await this.assertNameAvailable(data.name, farmId, transaction);
			return this.db.models.FeedType.create({
				farmId,
				name: data.name,
				notes: data.notes ?? null,
			}, { transaction });
		});
	}

	async updateFeedType(id: number, farmId: number, data: FeedTypeUpdate): Promise<FeedTypeModel | null> {
		return this.db.sequelize.transaction(async (transaction) => {
			const feedType = await this.db.models.FeedType.findOne({
				where: { id, farmId },
				transaction,
				lock: true,
			});

			if (!feedType) {
				return null;
			}

			if (data.name && data.name !== feedType.name) {
				await this.assertNameAvailable(data.name, farmId, transaction, id);
			}

			await feedType.update(data, { transaction });
			return feedType;
		});
	}

	async deleteFeedType(id: number, farmId: number): Promise<boolean> {
		return this.db.sequelize.transaction(async (transaction) => {
			const feedType = await this.db.models.FeedType.findOne({
				where: { id, farmId },
				transaction,
			});

			if (!feedType) {
				return false;
			}

			await feedType.destroy({ transaction });
			return true;
		});
	}

	private async assertNameAvailable(
		name: string,
		farmId: number,
		transaction: import('sequelize').Transaction,
		excludeId?: number,
	): Promise<void> {
		const where: Record<string, unknown> = { farmId, name };
		if (excludeId) {
			where.id = { [Op.ne]: excludeId };
		}
		const existing = await this.db.models.FeedType.findOne({ where, transaction });
		if (existing) {
			throw new Error('A feed type with this name already exists on this farm.');
		}
	}
}
