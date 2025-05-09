import { UserRole } from "../models/user-model";

export const authSignUpResponseSchema = {
	type: "object",
	properties: {
		message: { type: "string" },
	},
	required: ["message"],
	additionalProperties: false,
};

export const authLoginResponseSchema = {
	type: "object",
	properties: {
		message: { type: "string" },
	},
	required: ["message"],
	additionalProperties: false,
};
