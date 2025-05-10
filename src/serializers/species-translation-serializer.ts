import { SpeciesTranslation } from "../models/species-translation-model";
import { encodeId } from "../utils/id-hash-util";

export const createSpecieTranslationSchema = {
	type: "object",
	properties: {
		speciesId: { type: "string" },
		languageCode: { type: "string" },
		name: { type: "string" },
	},
	additionalProperties: false,
	required: ["speciesId", "languageCode", "name"],
};

export const deleteSpecieTranslationSchema = {
	type: "object",
	properties: {
		translationId: { type: "string" },
	},
	additionalProperties: false,
	required: ["translationId"],
};

export const serializeSpecieTranslation = (translation: SpeciesTranslation) => {
	return {
		id: encodeId(translation.id),
		speciesId: encodeId(translation.speciesId),
		languageCode: translation.languageCode,
		name: translation.name,
	};
};
