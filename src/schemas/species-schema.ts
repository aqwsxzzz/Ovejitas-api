export const speciesCreateSchema = {
	type: "object",
	required: ["name"],
	properties: {
		name: { type: "string", minLength: 1 },
		languageCode: { type: "string", minLength: 2, maxLength: 2 },
	},
	additionalProperties: false,
};
