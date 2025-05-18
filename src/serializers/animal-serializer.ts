import { Animal } from "../models/animal-model";
import { encodeId } from "../utils/id-hash-util";

export const animalResponseSchema = {
	type: "object",
	properties: {
		id: { type: "string" },
		farmId: { type: "string" },
		speciesId: { type: "string" },
		breedId: { type: ["string", "null"] },
		name: { type: "string" },
		tagNumber: { type: ["string", "null"] },
		sex: { type: "string" },
		birthDate: { type: "string", format: "date" },
		weight: { type: ["number", "null"] },
		status: { type: "string" },
		reproductiveStatus: { type: "string" },
		parentId: { type: ["string", "null"] },
		motherId: { type: ["string", "null"] },
		acquisitionType: { type: "string" },
		acquisitionDate: { type: "string", format: "date" },
		createdAt: { type: "string", format: "date-time" },
		updatedAt: { type: "string", format: "date-time" },
	},
	required: ["id", "farmId", "speciesId", "name", "sex", "birthDate", "status", "reproductiveStatus", "acquisitionType", "acquisitionDate", "createdAt", "updatedAt"],
	additionalProperties: false,
};

export function serializeAnimal(animal: Animal) {
	return {
		id: encodeId(animal.id),
		farmId: encodeId(animal.farmId),
		speciesId: encodeId(animal.speciesId),
		breedId: animal.breedId ? encodeId(animal.breedId) : null,
		name: animal.name,
		tagNumber: animal.tagNumber ?? null,
		sex: animal.sex,
		birthDate: animal.birthDate?.toISOString().split("T")[0],
		weight: animal.weight ?? null,
		status: animal.status,
		reproductiveStatus: animal.reproductiveStatus,
		parentId: animal.parentId ? encodeId(animal.parentId) : null,
		motherId: animal.motherId ? encodeId(animal.motherId) : null,
		acquisitionType: animal.acquisitionType,
		acquisitionDate: animal.acquisitionDate?.toISOString().split("T")[0],
		createdAt: animal.createdAt?.toISOString(),
		updatedAt: animal.updatedAt?.toISOString(),
	};
}
