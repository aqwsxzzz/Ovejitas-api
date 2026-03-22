import { BaseService } from '../../services/base.service';
import { FlockEventModel } from './flock-event.model';
import { FlockEventCreate, FlockEventType } from './flock-event.schema';
import { FindOptions } from 'sequelize';
import { PaginatedResult, PaginationParams } from '../../utils/pagination';

const SUBTRACTION_EVENTS: FlockEventType[] = [
	FlockEventType.Mortality,
	FlockEventType.Sale,
	FlockEventType.Cull,
];

export class FlockEventService extends BaseService {

	async getFlockEvents(flockId: number, pagination?: PaginationParams): Promise<PaginatedResult<FlockEventModel>> {
		const findOptions: FindOptions = {
			where: { flockId },
			order: [['date', 'DESC'], ['createdAt', 'DESC']],
		};

		return this.findAllPaginated(this.db.models.FlockEvent, findOptions, pagination!);
	}

	async createFlockEvent({ flockId, data, userId }: {
		flockId: number;
		data: FlockEventCreate;
		userId: number;
	}): Promise<FlockEventModel> {
		return this.db.sequelize.transaction(async (transaction) => {
			// Lock the flock row to prevent concurrent count updates
			const flock = await this.db.models.Flock.findByPk(flockId, {
				transaction,
				lock: true,
			});

			if (!flock) {
				throw new Error('Flock not found');
			}

			const isSubtraction = SUBTRACTION_EVENTS.includes(data.eventType);

			if (isSubtraction) {
				if (data.count > flock.currentCount) {
					throw new Error(`Cannot remove ${data.count} from flock. Current count is ${flock.currentCount}.`);
				}
			}

			// Create the event
			const event = await this.db.models.FlockEvent.create({
				flockId,
				eventType: data.eventType,
				count: data.count,
				date: data.date,
				reason: data.reason,
				recordedBy: userId,
			}, { transaction });

			// Update flock current count
			const countChange = isSubtraction ? -data.count : data.count;
			await flock.update({
				currentCount: flock.currentCount + countChange,
			}, { transaction });

			return event;
		});
	}

	async deleteFlockEvent({ flockId, eventId }: {
		flockId: number;
		eventId: number;
	}): Promise<void> {
		return this.db.sequelize.transaction(async (transaction) => {
			const event = await this.db.models.FlockEvent.findOne({
				where: { id: eventId, flockId },
				transaction,
			});

			if (!event) {
				throw new Error('Flock event not found');
			}

			// Lock the flock row
			const flock = await this.db.models.Flock.findByPk(flockId, {
				transaction,
				lock: true,
			});

			if (!flock) {
				throw new Error('Flock not found');
			}

			// Reverse the count change
			const isSubtraction = SUBTRACTION_EVENTS.includes(event.eventType);
			const reverseChange = isSubtraction ? event.count : -event.count;

			await flock.update({
				currentCount: flock.currentCount + reverseChange,
			}, { transaction });

			await event.destroy({ transaction });
		});
	}
}
