export const breedCreateSchema = {
	type: "object",
	required: ["speciesId", "name"],
	properties: {
		speciesId: { type: "string", minLength: 1 },
		name: { type: "string", minLength: 1 },
	},
	additionalProperties: false,
};

export const breedUpdateSchema = {
	type: "object",
	properties: {
		speciesId: { type: "string", minLength: 1 },
		name: { type: "string", minLength: 1 },
	},
	additionalProperties: false,
};

export const breedIdParamSchema = {
	type: "object",
	required: ["id"],
	properties: {
		id: { type: "string", minLength: 1 },
	},
	additionalProperties: false,
};
