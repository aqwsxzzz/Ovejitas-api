import { Species } from "../models/species-model";
import { SpeciesTranslation } from "../models/species-translation-model";
import { encodeId } from "../utils/id-hash-util";

export const speciesResponseSchema = {
	type: "object",
	properties: {
		id: { type: "string" },
		translation: {
			type: "object",
			properties: {
				id: { type: "string" },
				language: { type: "string" },
				name: { type: "string" },
			},
		},
		createdAt: { type: "string", format: "date-time" },
		updatedAt: { type: "string", format: "date-time" },
	},
	required: ["id", "translation", "createdAt", "updatedAt"],
	additionalProperties: false,
};

export function serializeSpecies(species: Species, translation?: SpeciesTranslation) {
	return {
		id: encodeId(species.id),
		translation: translation
			? {
					id: encodeId(translation.id),
					language: translation.languageCode,
					name: translation.name,
			  }
			: undefined,
		createdAt: species.createdAt,
		updatedAt: species.updatedAt,
	};
}
