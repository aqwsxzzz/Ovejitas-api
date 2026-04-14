import { FindOptions, Op } from 'sequelize';
import { BaseService } from '../../services/base.service';
import { FeedingScheduleModel } from './feeding-schedule.model';
import { FeedingScheduleCreate, FeedingScheduleUpdate } from './feeding-schedule.schema';
import { PaginatedResult, PaginationParams } from '../../utils/pagination';
import { decodeId } from '../../utils/id-hash-util';

export interface FeedingScheduleFilters {
	flockId?: number;
	feedTypeId?: number;
	activeOnly?: boolean;
}

export class FeedingScheduleService extends BaseService {
	async getFeedingSchedules(
		farmId: number,
		filters: FeedingScheduleFilters,
		pagination: PaginationParams,
	): Promise<PaginatedResult<FeedingScheduleModel>> {
		const where: Record<string, unknown> = { farmId };
		if (filters.flockId !== undefined) where.flockId = filters.flockId;
		if (filters.feedTypeId !== undefined) where.feedTypeId = filters.feedTypeId;
		if (filters.activeOnly) where.activeTo = null;

		const findOptions: FindOptions = {
			where,
			order: [['flockId', 'ASC'], ['feedTypeId', 'ASC']],
		};

		return this.findAllPaginated(this.db.models.FeedingSchedule, findOptions, pagination);
	}

	async getFeedingScheduleById(id: number, farmId: number): Promise<FeedingScheduleModel | null> {
		return this.db.models.FeedingSchedule.findOne({ where: { id, farmId } });
	}

	async createFeedingSchedule(farmId: number, data: FeedingScheduleCreate): Promise<FeedingScheduleModel> {
		const flockId = decodeId(data.flockId);
		if (!flockId) throw new Error('Invalid flock ID');
		const feedTypeId = decodeId(data.feedTypeId);
		if (!feedTypeId) throw new Error('Invalid feed type ID');

		return this.db.sequelize.transaction(async (transaction) => {
			const flock = await this.db.models.Flock.findOne({ where: { id: flockId, farmId }, transaction });
			if (!flock) throw new Error('Flock not found');

			const feedType = await this.db.models.FeedType.findOne({ where: { id: feedTypeId, farmId }, transaction });
			if (!feedType) throw new Error('Feed type not found');

			return this.db.models.FeedingSchedule.create({
				farmId,
				flockId,
				feedTypeId,
				qtyPerDay: data.qtyPerDay,
				activeFrom: data.activeFrom,
				activeTo: data.activeTo ?? null,
			}, { transaction });
		});
	}

	async updateFeedingSchedule(
		id: number,
		farmId: number,
		data: FeedingScheduleUpdate,
	): Promise<FeedingScheduleModel | null> {
		return this.db.sequelize.transaction(async (transaction) => {
			const schedule = await this.db.models.FeedingSchedule.findOne({
				where: { id, farmId },
				transaction,
				lock: true,
			});
			if (!schedule) return null;

			const updates: Record<string, unknown> = {};
			if (data.qtyPerDay !== undefined) updates.qtyPerDay = data.qtyPerDay;
			if (data.activeFrom !== undefined) updates.activeFrom = data.activeFrom;
			if (data.activeTo !== undefined) updates.activeTo = data.activeTo;

			await schedule.update(updates, { transaction });
			return schedule;
		});
	}

	async deleteFeedingSchedule(id: number, farmId: number): Promise<boolean> {
		return this.db.sequelize.transaction(async (transaction) => {
			const schedule = await this.db.models.FeedingSchedule.findOne({
				where: { id, farmId },
				transaction,
			});
			if (!schedule) return false;

			await schedule.destroy({ transaction });
			return true;
		});
	}

	async getActiveSchedulesForFlock(
		farmId: number,
		flockId: number,
		date: string,
		transaction?: import('sequelize').Transaction,
	): Promise<FeedingScheduleModel[]> {
		return this.db.models.FeedingSchedule.findAll({
			where: {
				farmId,
				flockId,
				activeFrom: { [Op.lte]: date },
				[Op.or]: [
					{ activeTo: null },
					{ activeTo: { [Op.gte]: date } },
				],
			},
			order: [['feedTypeId', 'ASC']],
			transaction,
		});
	}
}
