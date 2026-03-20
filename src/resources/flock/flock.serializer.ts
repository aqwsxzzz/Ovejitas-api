import { encodeId } from '../../utils/id-hash-util';
import { FlockResponse, FlockWithPossibleIncludes } from './flock.schema';

export class FlockSerializer {
	static serialize(flock: FlockWithPossibleIncludes): FlockResponse {
		const base: FlockResponse = {
			id: encodeId(flock.id),
			farmId: encodeId(flock.farmId),
			speciesId: encodeId(flock.speciesId),
			breedId: encodeId(flock.breedId),
			name: flock.name,
			flockType: flock.flockType as FlockResponse['flockType'],
			initialCount: flock.initialCount,
			currentCount: flock.currentCount,
			status: flock.status as FlockResponse['status'],
			startDate: flock.startDate,
			endDate: flock.endDate,
			houseName: flock.houseName,
			acquisitionType: flock.acquisitionType as FlockResponse['acquisitionType'],
			ageAtAcquisitionWeeks: flock.ageAtAcquisitionWeeks,
			notes: flock.notes,
			createdAt: flock.createdAt,
			updatedAt: flock.updatedAt,
		};

		if (flock.species) {
			base.species = {
				id: encodeId(flock.species.id),
				createdAt: flock.species.createdAt,
				updatedAt: flock.species.updatedAt,
				...(flock.species.translations && {
					translations: flock.species.translations.map(t => ({
						id: encodeId(t.id),
						language: t.language,
						name: t.name,
						createdAt: t.createdAt,
						updatedAt: t.updatedAt,
						speciesId: encodeId(t.speciesId),
					})),
				}),
			};
		}

		if (flock.breed) {
			base.breed = {
				id: encodeId(flock.breed.id),
				createdAt: flock.breed.createdAt,
				updatedAt: flock.breed.updatedAt,
				speciesId: encodeId(flock.breed.speciesId),
				...(flock.breed.translations && {
					translations: flock.breed.translations.map(t => ({
						id: encodeId(t.id),
						language: t.language,
						name: t.name,
						createdAt: t.createdAt,
						updatedAt: t.updatedAt,
						breedId: encodeId(t.breedId),
					})),
				}),
			};
		}

		return base;
	}

	static serializeMany(flocks: FlockWithPossibleIncludes[]): FlockResponse[] {
		return flocks.map(f => this.serialize(f));
	}
}
