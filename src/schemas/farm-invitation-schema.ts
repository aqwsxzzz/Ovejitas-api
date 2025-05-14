import { UserRole } from "../models/user-model";

const roleEnum = Object.values(UserRole);

export const farmInvitationCreateSchema = {
	params: {
		type: "object",
		properties: {
			farmId: { type: "string" }, // hashed
		},
		required: ["farmId"],
		additionalProperties: false,
	},
	body: {
		type: "object",
		properties: {
			email: { type: "string", format: "email" },
			role: { type: "string", enum: roleEnum },
		},
		required: ["email", "role"],
		additionalProperties: false,
	},
};

export const farmInvitationAcceptSchema = {
	body: {
		type: "object",
		properties: {
			token: { type: "string" },
			password: { type: "string", minLength: 6 },
			displayName: { type: "string", minLength: 1 },
			language: { type: "string" },
		},
		required: ["token", "password", "displayName"],
		additionalProperties: false,
	},
};

export const farmInvitationErrorResponseSchema = {
	type: "object",
	properties: {
		message: { type: "string" },
		code: { type: "string" },
	},
	required: ["message"],
	additionalProperties: true,
};
