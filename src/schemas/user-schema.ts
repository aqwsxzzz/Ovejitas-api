import { UserRole } from "../models/user-model";

export const userCreateSchema = {
	type: "object",
	required: ["displayName", "email", "password"],
	properties: {
		displayName: { type: "string", minLength: 1 },
		email: { type: "string", format: "email" },
		password: { type: "string", minLength: 8 },
		isActive: { type: "boolean" },
		role: { type: "string", enum: Object.values(UserRole) },
	},
	additionalProperties: false,
};

export const userUpdateSchema = {
	type: "object",
	properties: {
		displayName: { type: "string", minLength: 1 },
		email: { type: "string", format: "email" },
		password: { type: "string", minLength: 8 },
		isActive: { type: "boolean" },
		role: { type: "string", enum: Object.values(UserRole) },
	},
	additionalProperties: false,
};
