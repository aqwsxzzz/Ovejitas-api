import { Animal } from "../models/animal-model";
import { encodeId } from "../utils/id-hash-util";
import { Species } from "../models/species-model";
import { Breed } from "../models/breed-model";
import { SpeciesTranslation } from "../models/species-translation-model";

export const animalResponseSchema = {
	type: "object",
	properties: {
		id: { type: "string" },
		farmId: { type: "string" },
		species: {
			type: "object",
			properties: {
				id: { type: "string" },
				name: { type: "string" },
			},
			required: ["id", "name"],
		},
		breed: {
			type: "object",
			properties: {
				id: { type: "string" },
				name: { type: "string" },
			},
			required: ["id", "name"],
		},
		name: { type: "string" },
		tagNumber: { type: "string" },
		sex: { type: "string" },
		birthDate: { type: "string", format: "date" },
		weight: { type: ["number", "null"] },
		status: { type: "string" },
		reproductiveStatus: { type: "string" },
		fatherId: { type: ["string", "null"] },
		motherId: { type: ["string", "null"] },
		acquisitionType: { type: "string" },
		acquisitionDate: { type: "string", format: "date" },
		createdAt: { type: "string", format: "date-time" },
		updatedAt: { type: "string", format: "date-time" },
	},
	required: ["id", "farmId", "species", "breed", "name", "tagNumber", "sex", "birthDate", "status", "reproductiveStatus", "acquisitionType", "acquisitionDate", "createdAt", "updatedAt"],
	additionalProperties: false,
};

export function serializeAnimal(animal: Animal, language: string) {
	const animalWithAssociations = animal as Animal & {
		species?: Species & { translations?: SpeciesTranslation[] };
		breed?: Breed;
	};

	const species = animalWithAssociations.species;
	const breed = animalWithAssociations.breed;

	// Get species name from translations or use a default
	const speciesName = species?.translations && species.translations.length > 0 ? species.translations.find((translation) => translation.languageCode === language)?.name : "Unknown Species";

	return {
		id: encodeId(animal.id),
		farmId: encodeId(animal.farmId),
		species: {
			id: encodeId(animal.speciesId),
			name: speciesName,
		},
		breed: breed
			? {
					id: encodeId(breed.id),
					name: breed.name,
			  }
			: {
					id: encodeId(animal.breedId),
					name: "Unknown Breed",
			  },
		name: animal.name,
		tagNumber: animal.tagNumber,
		sex: animal.sex,
		birthDate: animal.birthDate?.toISOString().split("T")[0],
		weight: animal.weight ?? null,
		status: animal.status,
		reproductiveStatus: animal.reproductiveStatus,
		fatherId: animal.fatherId ? encodeId(animal.fatherId) : null,
		motherId: animal.motherId ? encodeId(animal.motherId) : null,
		acquisitionType: animal.acquisitionType,
		acquisitionDate: animal.acquisitionDate?.toISOString().split("T")[0],
		createdAt: animal.createdAt?.toISOString(),
		updatedAt: animal.updatedAt?.toISOString(),
	};
}
