import { Farm } from "../models/farm-model";
import { encodeId } from "../utils/id-hash-util";

export const farmResponseSchema = {
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

export function serializeFarm(farm: Farm) {
	return {
		id: encodeId(farm.id),
		name: farm.name,
		createdAt: farm.createdAt,
		updatedAt: farm.updatedAt,
	};
}
