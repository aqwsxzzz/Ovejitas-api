import { encodeId } from '../../utils/id-hash-util';
import { AnimalModel } from './animal.model';
import { AnimalResponse } from './animal.schema';

export class AnimalSerializer {
	static serialize(animal: AnimalModel): AnimalResponse {
		return {
			id: encodeId(animal.id),
			farmId: animal.farmId,
			speciesId: encodeId(animal.speciesId),
			breedId: encodeId(animal.breedId),
			name: animal.name,
			tagNumber: animal.tagNumber,
			sex: animal.sex as AnimalResponse['sex'],
			birthDate: animal.birthDate,
			weight: animal.weight ?? undefined,
			status: animal.status as AnimalResponse['status'],
			reproductiveStatus: animal.reproductiveStatus as AnimalResponse['reproductiveStatus'],
			fatherId: animal.fatherId ? encodeId(animal.fatherId) : '',
			motherId: animal.motherId ? encodeId(animal.motherId) : '',
			acquisitionType: animal.acquisitionType as AnimalResponse['acquisitionType'],
			acquisitionDate: animal.acquisitionDate,
			createdAt: animal.createdAt,
			updatedAt: animal.updatedAt,
		};
	}

	static serializeMany(animals: AnimalModel[]): AnimalResponse[] {
		return animals.map(a => this.serialize(a));
	}
}
