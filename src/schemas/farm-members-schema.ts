import type { FarmMemberRole } from "../types/farm-members-types";

const roleEnum: FarmMemberRole[] = ["owner", "member"];

export const farmMembersCreateSchema = {
	params: {
		type: "object",
		properties: {
			farmId: { type: "string" },
		},
		required: ["farmId"],
		additionalProperties: false,
	},
	body: {
		type: "object",
		properties: {
			userId: { type: "string" },
			role: { type: "string", enum: roleEnum },
		},
		required: ["userId", "role"],
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

export const farmMembersFarmIdParamSchema = {
	params: {
		type: "object",
		properties: {
			farmId: { type: "string" },
		},
		required: ["farmId"],
		additionalProperties: false,
	},
};

export const farmMembersFarmIdAndMemberIdParamSchema = {
	params: {
		type: "object",
		properties: {
			farmId: { type: "string" },
			memberId: { type: "string" },
		},
		required: ["farmId", "memberId"],
		additionalProperties: false,
	},
};
