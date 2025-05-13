import { FarmMembers } from "../models/farm-members-model";
import { User } from "../models/user-model";
import { encodeId } from "../utils/id-hash-util";
import type { FarmMemberRole } from "../types/farm-members-types";
import { serializeUser } from "./user-serializer";
import { userResponseSchema } from "./user-serializer";

const roleEnum: FarmMemberRole[] = ["owner", "member"];

// Type for FarmMembers instance with included user
export type FarmMembersWithUser = FarmMembers & { user?: User };

export const farmMembersResponseSchema = {
	type: "object",
	properties: {
		id: { type: "string" },
		user: {
			type: "object",
			properties: {
				id: { type: "string" },
				displayName: { type: "string" },
				email: { type: "string" },
			},
			required: ["id", "displayName", "email"],
			additionalProperties: false,
		},
		role: { type: "string", enum: roleEnum },
		createdAt: { type: "string", format: "date-time" },
		updatedAt: { type: "string", format: "date-time" },
	},
	required: ["id", "user", "role", "createdAt", "updatedAt"],
	additionalProperties: false,
};

export const farmMembersArrayResponseSchema = {
	type: "array",
	items: farmMembersResponseSchema,
};

export function serializeFarmMembers(farmMember: FarmMembersWithUser) {
	return {
		id: encodeId(farmMember.id),
		farmId: encodeId(farmMember.farmId),
		user: farmMember.user ? serializeUser(farmMember.user) : null,
		role: farmMember.role,
		createdAt: farmMember.createdAt,
		updatedAt: farmMember.updatedAt,
	};
}

export function serializeFarmMembersArray(farmMembers: FarmMembersWithUser[]) {
	return farmMembers.map(serializeFarmMembers);
}
