import type { FarmMemberRole } from "../types/farm-members-types";

const roleEnum: FarmMemberRole[] = ["owner", "member"];

export const farmMembersCreateSchema = {
	body: {
		type: "object",
		properties: {
			farmId: { type: "string" },
			userId: { type: "string" },
			role: { type: "string", enum: roleEnum },
		},
		required: ["farmId", "userId", "role"],
		additionalProperties: false,
	},
};

export const farmMembersUpdateSchema = {
	params: {
		type: "object",
		properties: {
			id: { type: "string" },
		},
		required: ["id"],
		additionalProperties: false,
	},
	body: {
		type: "object",
		properties: {
			role: { type: "string", enum: roleEnum },
		},
		required: ["role"],
		additionalProperties: false,
	},
};

export const farmMembersIdParamSchema = {
	params: {
		type: "object",
		properties: {
			id: { type: "string" },
		},
		required: ["id"],
		additionalProperties: false,
	},
};
