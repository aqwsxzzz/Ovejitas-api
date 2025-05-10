export const speciesCreateSchema = {
	type: "object",
	required: ["name"],
	properties: {
		name: { type: "string", minLength: 1 },
	},
	additionalProperties: false,
};

export const speciesUpdateSchema = {
	type: "object",
	properties: {
		name: { type: "string", minLength: 1 },
	},
	additionalProperties: false,
};
