import { encodeId } from '../../utils/id-hash-util';
import { EggCollectionResponse } from './egg-collection.schema';
import { EggCollectionModel } from './egg-collection.model';

export class EggCollectionSerializer {
	static serialize(collection: EggCollectionModel, currentCount: number): EggCollectionResponse {
		const usableEggs = collection.totalEggs - collection.brokenEggs;
		const layRate = currentCount > 0
			? Number(((collection.totalEggs / currentCount) * 100).toFixed(2))
			: 0;

		return {
			id: encodeId(collection.id),
			flockId: encodeId(collection.flockId),
			date: collection.date,
			totalEggs: collection.totalEggs,
			brokenEggs: collection.brokenEggs,
			collectedBy: collection.collectedBy ? encodeId(collection.collectedBy) : null,
			notes: collection.notes,
			usableEggs,
			layRate,
			createdAt: collection.createdAt,
			updatedAt: collection.updatedAt,
		};
	}

	static serializeMany(collections: EggCollectionModel[], currentCount: number): EggCollectionResponse[] {
		return collections.map(c => this.serialize(c, currentCount));
	}
}
