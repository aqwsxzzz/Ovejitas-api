import { UserRole } from "../models/user-model";

export const authSignUpSchema = {
	type: "object",
	required: ["displayName", "email", "password"],
	properties: {
		displayName: { type: "string", minLength: 1 },
		email: { type: "string", format: "email" },
		password: { type: "string", minLength: 8 },
		role: { type: "string", enum: Object.values(UserRole) },
	},
	additionalProperties: false,
};

export const authLoginSchema = {
	type: "object",
	required: ["email", "password"],
	properties: {
		email: { type: "string", format: "email" },
		password: { type: "string", minLength: 8 },
	},
	additionalProperties: false,
};
