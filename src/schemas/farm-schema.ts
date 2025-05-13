export const farmCreateSchema = {
	type: "object",
	required: ["name"],
	properties: {
		name: { type: "string", minLength: 1 },
	},
	additionalProperties: false,
};

export const farmUpdateSchema = {
	type: "object",
	required: ["name"],
	properties: {
		name: { type: "string", minLength: 1 },
	},
	additionalProperties: false,
};
