export const animalCreateSchema = {
	type: "object",
	required: ["speciesId", "name", "sex", "birthDate", "status", "reproductiveStatus", "acquisitionType", "acquisitionDate"],
	properties: {
		speciesId: { type: "string", minLength: 1 },
		// breedId must belong to the provided speciesId. If not, a 400 error is returned.
		breedId: { type: ["string", "null"], minLength: 1 },
		name: { type: "string", minLength: 1 },
		tagNumber: { type: ["string", "null"], minLength: 1 },
		sex: { type: "string", enum: ["male", "female", "unknown"] },
		birthDate: { type: "string", format: "date" },
		weight: { type: ["number", "null"] },
		status: { type: "string", enum: ["alive", "sold", "deceased"] },
		reproductiveStatus: { type: "string", enum: ["open", "pregnant", "lactating", "other"] },
		fatherId: { type: ["string", "null"], minLength: 1 },
		motherId: { type: ["string", "null"], minLength: 1 },
		acquisitionType: { type: "string", enum: ["born", "purchased", "other"] },
		acquisitionDate: { type: "string", format: "date" },
	},
	additionalProperties: false,
};

export const animalUpdateSchema = {
	type: "object",
	properties: {
		speciesId: { type: "string", minLength: 1 },
		breedId: { type: ["string", "null"], minLength: 1 },
		name: { type: "string", minLength: 1 },
		tagNumber: { type: ["string", "null"], minLength: 1 },
		sex: { type: "string", enum: ["male", "female", "unknown"] },
		birthDate: { type: "string", format: "date" },
		weight: { type: ["number", "null"] },
		status: { type: "string", enum: ["alive", "sold", "deceased"] },
		reproductiveStatus: { type: "string", enum: ["open", "pregnant", "lactating", "other"] },
		fatherId: { type: ["string", "null"], minLength: 1 },
		motherId: { type: ["string", "null"], minLength: 1 },
		acquisitionType: { type: "string", enum: ["born", "purchased", "other"] },
		acquisitionDate: { type: "string", format: "date" },
	},
	additionalProperties: false,
};

export const animalIdParamSchema = {
	type: "object",
	required: ["id"],
	properties: {
		id: { type: "string", minLength: 1 },
	},
	additionalProperties: false,
};

export const animalListParamSchema = {
	type: "object",
	required: ["farmId"],
	properties: {
		farmId: { type: "string", minLength: 1 },
	},
	additionalProperties: false,
};

export const animalCreateWithFarmParamSchema = {
	params: {
		type: "object",
		required: ["farmId"],
		properties: {
			farmId: { type: "string", minLength: 1 },
		},
		additionalProperties: false,
	},
	body: {
		type: "object",
		required: ["speciesId", "name", "sex", "birthDate", "status", "reproductiveStatus", "acquisitionType", "acquisitionDate"],
		properties: animalCreateSchema,
		additionalProperties: false,
	},
};
