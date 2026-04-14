import { encodeId } from '../../utils/id-hash-util';
import { FeedingScheduleModel } from './feeding-schedule.model';
import { FeedingScheduleResponse } from './feeding-schedule.schema';

export class FeedingScheduleSerializer {
	static serialize(schedule: FeedingScheduleModel): FeedingScheduleResponse {
		return {
			id: encodeId(schedule.id),
			farmId: encodeId(schedule.farmId),
			flockId: encodeId(schedule.flockId),
			feedTypeId: encodeId(schedule.feedTypeId),
			qtyPerDay: Number(schedule.qtyPerDay),
			activeFrom: schedule.activeFrom,
			activeTo: schedule.activeTo,
			createdAt: schedule.createdAt,
			updatedAt: schedule.updatedAt,
		};
	}

	static serializeMany(schedules: FeedingScheduleModel[]): FeedingScheduleResponse[] {
		return schedules.map(s => this.serialize(s));
	}
}
