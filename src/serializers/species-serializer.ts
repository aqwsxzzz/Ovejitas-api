import { Species } from "../models/species-model";
import { encodeId } from "../utils/id-hash-util";

export const speciesResponseSchema = {
	type: "object",
	properties: {
		id: { type: "string" },
		name: { type: "string" },
		createdAt: { type: "string", format: "date-time" },
		updatedAt: { type: "string", format: "date-time" },
	},
	required: ["id", "name", "createdAt", "updatedAt"],
	additionalProperties: false,
};

// Optionally, a serializer function for output shaping
export function serializeSpecies(species: Species) {
	return {
		id: encodeId(species.id),
		name: species.name,
		createdAt: species.createdAt,
		updatedAt: species.updatedAt,
	};
}
