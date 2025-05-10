export const speciesTranslationCreateSchema = {
	type: "object",
	properties: {
		speciesId: { type: "string" },
		languageCode: { type: "string" },
		name: { type: "string" },
	},
	required: ["speciesId", "languageCode", "name"],
	additionalProperties: false,
};

export const speciesTranslationDeleteSchema = {
	type: "object",
	properties: {
		translationId: { type: "string" },
	},
	required: ["translationId"],
	additionalProperties: false,
};
