import { encodeId } from '../../utils/id-hash-util';
import { BreedModel } from './breed.model';
import { BreedResponse } from './breed.schema';

export class BreedSerializer {
	static serialize(breed: BreedModel): BreedResponse {
		return {
			id: encodeId(breed.id),
			name: breed.name,
			speciesId: encodeId(breed.speciesId),
			createdAt: breed.createdAt,
			updatedAt: breed.updatedAt,
		};
	}
}
