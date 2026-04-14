import { encodeId } from '../../utils/id-hash-util';
import { FeedTypeModel } from './feed-type.model';
import { FeedTypeResponse } from './feed-type.schema';

export class FeedTypeSerializer {
	static serialize(feedType: FeedTypeModel): FeedTypeResponse {
		return {
			id: encodeId(feedType.id),
			farmId: encodeId(feedType.farmId),
			name: feedType.name,
			notes: feedType.notes,
			createdAt: feedType.createdAt,
			updatedAt: feedType.updatedAt,
		};
	}

	static serializeMany(feedTypes: FeedTypeModel[]): FeedTypeResponse[] {
		return feedTypes.map(f => this.serialize(f));
	}
}
