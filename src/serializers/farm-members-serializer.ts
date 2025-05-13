import { FarmMembers } from "../models/farm-members-model";
import { encodeId } from "../utils/id-hash-util";
import type { FarmMemberRole } from "../types/farm-members-types";

const roleEnum: FarmMemberRole[] = ["owner", "member"];

export const farmMembersResponseSchema = {
	type: "object",
	properties: {
		id: { type: "string" },
		farmId: { type: "string" },
		userId: { type: "string" },
		role: { type: "string", enum: roleEnum },
		createdAt: { type: "string", format: "date-time" },
		updatedAt: { type: "string", format: "date-time" },
	},
	required: ["id", "farmId", "userId", "role", "createdAt", "updatedAt"],
	additionalProperties: false,
};

export function serializeFarmMembers(farmMember: FarmMembers) {
	return {
		id: encodeId(farmMember.id),
		farmId: encodeId(farmMember.farmId),
		userId: encodeId(farmMember.userId),
		role: farmMember.role,
		createdAt: farmMember.createdAt,
		updatedAt: farmMember.updatedAt,
	};
}
