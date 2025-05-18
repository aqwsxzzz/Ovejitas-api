import { Breed } from "../models/breed-model";
import { encodeId } from "../utils/id-hash-util";

export const breedResponseSchema = {
	type: "object",
	properties: {
		id: { type: "string" },
		speciesId: { type: "string" },
		name: { type: "string" },
		createdAt: { type: "string", format: "date-time" },
		updatedAt: { type: "string", format: "date-time" },
	},
	required: ["id", "speciesId", "name", "createdAt", "updatedAt"],
	additionalProperties: false,
};

export function serializeBreed(breed: Breed) {
	return {
		id: encodeId(breed.id),
		speciesId: encodeId(breed.speciesId),
		name: breed.name,
		createdAt: breed.createdAt,
		updatedAt: breed.updatedAt,
	};
}
