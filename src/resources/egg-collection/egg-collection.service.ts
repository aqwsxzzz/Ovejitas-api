import { BaseService } from '../../services/base.service';
import { EggCollectionModel } from './egg-collection.model';
import { EggCollectionCreate, EggCollectionUpdate } from './egg-collection.schema';
import { FindOptions, Op } from 'sequelize';
import { PaginatedResult, PaginationParams } from '../../utils/pagination';
import { FlockStatus } from '../flock/flock.schema';

export class EggCollectionService extends BaseService {

	async getEggCollections(flockId: number, pagination?: PaginationParams): Promise<PaginatedResult<EggCollectionModel>> {
		const findOptions: FindOptions = {
			where: { flockId },
			order: [['date', 'DESC']],
		};

		return this.findAllPaginated(this.db.models.EggCollection, findOptions, pagination!);
	}

	async createEggCollection({ flockId, data, userId }: {
		flockId: number;
		data: EggCollectionCreate;
		userId: number;
	}): Promise<EggCollectionModel> {
		return this.db.sequelize.transaction(async (transaction) => {
			const flock = await this.db.models.Flock.findByPk(flockId, { transaction });

			if (!flock) {
				throw new Error('Flock not found');
			}

			if (flock.status !== FlockStatus.Active) {
				throw new Error('Cannot add egg collection to an inactive flock.');
			}

			const brokenEggs = data.brokenEggs ?? 0;
			if (brokenEggs > data.totalEggs) {
				throw new Error('Broken eggs cannot exceed total eggs.');
			}

			// Validate unique date per flock
			const existing = await this.db.models.EggCollection.findOne({
				where: { flockId, date: data.date },
				transaction,
			});

			if (existing) {
				throw new Error('An egg collection already exists for this flock on this date.');
			}

			return this.db.models.EggCollection.create({
				flockId,
				date: data.date,
				totalEggs: data.totalEggs,
				brokenEggs,
				collectedBy: userId,
				notes: data.notes,
			}, { transaction });
		});
	}

	async updateEggCollection({ flockId, collectionId, data }: {
		flockId: number;
		collectionId: number;
		data: EggCollectionUpdate;
	}): Promise<EggCollectionModel> {
		return this.db.sequelize.transaction(async (transaction) => {
			const collection = await this.db.models.EggCollection.findOne({
				where: { id: collectionId, flockId },
				transaction,
				lock: true,
			});

			if (!collection) {
				throw new Error('Egg collection not found');
			}

			const totalEggs = data.totalEggs ?? collection.totalEggs;
			const brokenEggs = data.brokenEggs ?? collection.brokenEggs;

			if (brokenEggs > totalEggs) {
				throw new Error('Broken eggs cannot exceed total eggs.');
			}

			await collection.update(data, { transaction });

			return collection;
		});
	}

	async deleteEggCollection({ flockId, collectionId }: {
		flockId: number;
		collectionId: number;
	}): Promise<void> {
		return this.db.sequelize.transaction(async (transaction) => {
			const collection = await this.db.models.EggCollection.findOne({
				where: { id: collectionId, flockId },
				transaction,
			});

			if (!collection) {
				throw new Error('Egg collection not found');
			}

			await collection.destroy({ transaction });
		});
	}
}
