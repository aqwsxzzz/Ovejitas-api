import { UserRole } from "../models/user-model";

export const userResponseSchema = {
	type: "object",
	properties: {
		id: { type: "number" },
		displayName: { type: "string" },
		email: { type: "string" },
		isActive: { type: "boolean" },
		role: { type: "string", enum: Object.values(UserRole) },
		createdAt: { type: "string", format: "date-time" },
		updatedAt: { type: "string", format: "date-time" },
	},
	required: ["id", "displayName", "email", "isActive", "role", "createdAt", "updatedAt"],
	additionalProperties: false,
};
