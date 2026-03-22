import { encodeId } from '../../utils/id-hash-util';
import { FlockEventResponse } from './flock-event.schema';
import { FlockEventModel } from './flock-event.model';

export class FlockEventSerializer {
	static serialize(event: FlockEventModel): FlockEventResponse {
		return {
			id: encodeId(event.id),
			flockId: encodeId(event.flockId),
			eventType: event.eventType,
			count: event.count,
			date: event.date,
			reason: event.reason,
			recordedBy: event.recordedBy ? encodeId(event.recordedBy) : null,
			createdAt: event.createdAt,
			updatedAt: event.updatedAt,
		};
	}

	static serializeMany(events: FlockEventModel[]): FlockEventResponse[] {
		return events.map(e => this.serialize(e));
	}
}
