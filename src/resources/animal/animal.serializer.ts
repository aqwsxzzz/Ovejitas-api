import { encodeId } from '../../utils/id-hash-util';
import { AnimalResponse, AnimalWithIncludes, AnimalWithPossibleIncludes } from './animal.schema';
import { AnimalMeasurementResponse } from '../animal-measurement/animal-measurement.schema';

export class AnimalSerializer {
	static serialize(animal: AnimalWithPossibleIncludes): AnimalResponse {
		const base = {
			id: encodeId(animal.id),
			farmId: encodeId(animal.farmId)!,
			speciesId: encodeId(animal.speciesId),
			breedId: encodeId(animal.breedId),
			name: animal.name,
			tagNumber: animal.tagNumber,
			sex: animal.sex as AnimalResponse['sex'],
			birthDate: animal.birthDate,
			status: animal.status as AnimalResponse['status'],
			reproductiveStatus: animal.reproductiveStatus as AnimalResponse['reproductiveStatus'],
			fatherId: animal.fatherId ? encodeId(animal.fatherId) : '',
			motherId: animal.motherId ? encodeId(animal.motherId) : '',
			acquisitionType: animal.acquisitionType as AnimalResponse['acquisitionType'],
			acquisitionDate: animal.acquisitionDate,
			createdAt: animal.createdAt,
			updatedAt: animal.updatedAt,
			weightId: animal.weightId ? encodeId(animal.weightId) : '',
			groupName: animal.groupName,
		};

		const result: AnimalWithIncludes = { ...base };

		if (animal.species) {
			result.species = {
				id: encodeId(animal.species.id),
				createdAt: animal.species.createdAt,
				updatedAt: animal.species.updatedAt,
				...(animal.species.translations && {
					translations: animal.species.translations.map(t => ({
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

		if (animal.breed) {
			result.breed = {
				id: encodeId(animal.breed.id),
				name: animal.breed.name,
				createdAt: animal.breed.createdAt,
				updatedAt: animal.breed.updatedAt,
				speciesId: encodeId(animal.breed.speciesId),
			};
		}

		if (animal.father) {
			result.father = {
				id: encodeId(animal.father.id),
				name: animal.father.name,
				createdAt: animal.father.createdAt,
				updatedAt: animal.father.updatedAt,
				tagNumber: animal.father.tagNumber,
			};
		}

		if (animal.mother) {
			result.mother = {
				id: encodeId(animal.mother.id),
				name: animal.mother.name,
				createdAt: animal.mother.createdAt,
				updatedAt: animal.mother.updatedAt,
				tagNumber: animal.mother.tagNumber,

			};
		}

		if (animal.measurements && animal.measurements.length > 0) {
			const lastMeasurement = animal.measurements[0]; // Since we ordered by measuredAt DESC with limit 1
			result.lastMeasurement = {
				id: encodeId(lastMeasurement.id),
				animalId: encodeId(lastMeasurement.animalId),
				measurementType: lastMeasurement.measurementType,
				value: lastMeasurement.value,
				unit: lastMeasurement.unit,
				measuredAt: lastMeasurement.measuredAt,
				measuredBy: encodeId(lastMeasurement.measuredBy),
				notes: lastMeasurement.notes,
				createdAt: lastMeasurement.createdAt,
				updatedAt: lastMeasurement.updatedAt,
			} as AnimalMeasurementResponse;
		}

		return result;
	}

	static serializeMany(animals: AnimalWithPossibleIncludes[]): AnimalResponse[] {
		return animals.map(a => this.serialize(a));
	}
}
