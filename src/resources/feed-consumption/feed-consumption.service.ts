import { FindOptions, Op } from 'sequelize';
import { BaseService } from '../../services/base.service';
import { FeedConsumptionModel } from './feed-consumption.model';
import { FeedConsumptionLotModel } from './feed-consumption-lot.model';
import { FeedConsumptionCreate, FeedConsumptionReason } from './feed-consumption.schema';
import { PaginatedResult, PaginationParams } from '../../utils/pagination';
import { decodeId } from '../../utils/id-hash-util';
import { drainFIFO } from './feed-consumption-fifo';
import { FeedingScheduleModel } from '../feeding-schedule/feeding-schedule.model';

export interface FeedConsumptionFilters {
	flockId?: number;
	feedTypeId?: number;
	from?: string;
	to?: string;
}

export class FeedConsumptionService extends BaseService {
	async getFeedConsumptions(
		farmId: number,
		filters: FeedConsumptionFilters,
		includeLots: boolean,
		pagination: PaginationParams,
	): Promise<PaginatedResult<FeedConsumptionModel>> {
		const where: Record<string, unknown> = { farmId };
		if (filters.flockId !== undefined) where.flockId = filters.flockId;
		if (filters.feedTypeId !== undefined) where.feedTypeId = filters.feedTypeId;
		if (filters.from || filters.to) {
			const range: Record<symbol, string> = {};
			if (filters.from) range[Op.gte] = filters.from;
			if (filters.to) range[Op.lte] = filters.to;
			where.consumedAt = range;
		}

		const findOptions: FindOptions = {
			where,
			order: [['consumedAt', 'DESC'], ['id', 'DESC']],
			...(includeLots && {
				include: [{ model: this.db.models.FeedConsumptionLot, as: 'lots' }],
			}),
		};

		return this.findAllPaginated(this.db.models.FeedConsumption, findOptions, pagination);
	}

	async getFeedConsumptionById(id: number, farmId: number): Promise<FeedConsumptionModel | null> {
		return this.db.models.FeedConsumption.findOne({
			where: { id, farmId },
			include: [{ model: this.db.models.FeedConsumptionLot, as: 'lots' }],
		});
	}

	async createFeedConsumption(
		farmId: number,
		createdBy: number,
		data: FeedConsumptionCreate,
	): Promise<FeedConsumptionModel> {
		const feedTypeId = decodeId(data.feedTypeId);
		if (!feedTypeId) {
			throw new Error('Invalid feed type ID');
		}

		const flockId = data.flockId ? decodeId(data.flockId) : null;
		if (data.flockId && !flockId) {
			throw new Error('Invalid flock ID');
		}

		if (data.reason === FeedConsumptionReason.Feeding && !flockId) {
			throw new Error('A flock is required when reason is "feeding".');
		}

		return this.db.sequelize.transaction(async (transaction) => {
			const feedType = await this.db.models.FeedType.findOne({
				where: { id: feedTypeId, farmId },
				transaction,
			});
			if (!feedType) {
				throw new Error('Feed type not found');
			}

			if (flockId !== null) {
				const flock = await this.db.models.Flock.findOne({
					where: { id: flockId, farmId },
					transaction,
				});
				if (!flock) {
					throw new Error('Flock not found');
				}
			}

			const draws = await drainFIFO(
				this.db,
				{ farmId, feedTypeId, qty: data.qty },
				transaction,
			);

			const consumption = await this.db.models.FeedConsumption.create({
				farmId,
				flockId,
				feedTypeId,
				consumedAt: data.consumedAt,
				qty: data.qty,
				reason: data.reason,
				notes: data.notes ?? null,
				createdBy,
			}, { transaction });

			await this.db.models.FeedConsumptionLot.bulkCreate(
				draws.map(draw => ({
					consumptionId: consumption.id,
					lotId: draw.lotId,
					qtyDrawn: draw.qtyDrawn,
					unitPriceSnapshot: draw.unitPriceSnapshot,
				})),
				{ transaction },
			);

			return this.db.models.FeedConsumption.findByPk(consumption.id, {
				include: [{ model: this.db.models.FeedConsumptionLot, as: 'lots' }],
				transaction,
			}) as Promise<FeedConsumptionModel>;
		});
	}

	async logTodaysFeeding(
		farmId: number,
		flockId: number,
		createdBy: number,
		date: string,
	): Promise<FeedConsumptionModel[]> {
		return this.db.sequelize.transaction(async (transaction) => {
			const flock = await this.db.models.Flock.findOne({ where: { id: flockId, farmId }, transaction });
			if (!flock) throw new Error('Flock not found');

			const schedules = await this.db.models.FeedingSchedule.findAll({
				where: {
					farmId,
					flockId,
					activeFrom: { [Op.lte]: date },
					[Op.or]: [{ activeTo: null }, { activeTo: { [Op.gte]: date } }],
				},
				order: [['feedTypeId', 'ASC']],
				transaction,
			}) as FeedingScheduleModel[];

			if (schedules.length === 0) {
				throw new Error('No active feeding schedules found for this flock.');
			}

			const created: FeedConsumptionModel[] = [];

			for (const schedule of schedules) {
				const draws = await drainFIFO(
					this.db,
					{ farmId, feedTypeId: schedule.feedTypeId, qty: Number(schedule.qtyPerDay) },
					transaction,
				);

				const consumption = await this.db.models.FeedConsumption.create({
					farmId,
					flockId,
					feedTypeId: schedule.feedTypeId,
					consumedAt: date,
					qty: Number(schedule.qtyPerDay),
					reason: FeedConsumptionReason.Feeding,
					notes: null,
					createdBy,
				}, { transaction });

				await this.db.models.FeedConsumptionLot.bulkCreate(
					draws.map(draw => ({
						consumptionId: consumption.id,
						lotId: draw.lotId,
						qtyDrawn: draw.qtyDrawn,
						unitPriceSnapshot: draw.unitPriceSnapshot,
					})),
					{ transaction },
				);

				const reloaded = await this.db.models.FeedConsumption.findByPk(consumption.id, {
					include: [{ model: this.db.models.FeedConsumptionLot, as: 'lots' }],
					transaction,
				}) as FeedConsumptionModel;
				created.push(reloaded);
			}

			return created;
		});
	}

	async deleteFeedConsumption(id: number, farmId: number): Promise<boolean> {
		return this.db.sequelize.transaction(async (transaction) => {
			const consumption = await this.db.models.FeedConsumption.findOne({
				where: { id, farmId },
				transaction,
				lock: true,
			});
			if (!consumption) {
				return false;
			}

			const drawnLots = await this.db.models.FeedConsumptionLot.findAll({
				where: { consumptionId: consumption.id },
				transaction,
			});

			for (const drawn of drawnLots) {
				await this.db.models.FeedLot.increment('qtyRemaining', {
					by: Number(drawn.qtyDrawn),
					where: { id: drawn.lotId },
					transaction,
				});
			}

			// CASCADE on consumption_id deletes feed_consumption_lot rows
			await consumption.destroy({ transaction });
			return true;
		});
	}
}

export type FeedConsumptionWithLots = FeedConsumptionModel & {
	lots?: FeedConsumptionLotModel[];
};
