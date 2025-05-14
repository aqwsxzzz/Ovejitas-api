import { FarmInvitation } from "../models/farm-invitation-model";
import { encodeId } from "../utils/id-hash-util";
import { UserRole } from "../models/user-model";
import { FarmInvitationStatus } from "../types/farm-invitation-types";

export function serializeFarmInvitation(invitation: FarmInvitation, includeToken = false) {
	return {
		id: encodeId(Number(invitation.id)),
		email: invitation.email,
		farmId: encodeId(Number(invitation.farmId)),
		role: invitation.role,
		status: invitation.status,
		createdAt: invitation.createdAt,
		updatedAt: invitation.updatedAt,
		...(includeToken ? { token: invitation.token } : {}),
	};
}

export const farmInvitationResponseSchema = {
	type: "object",
	properties: {
		id: { type: "string" },
		email: { type: "string", format: "email" },
		farmId: { type: "string" },
		role: { type: "string", enum: Object.values(UserRole) },
		status: { type: "string", enum: ["pending", "accepted", "expired", "cancelled"] as FarmInvitationStatus[] },
		createdAt: { type: "string", format: "date-time" },
		updatedAt: { type: "string", format: "date-time" },
		token: { type: "string" },
	},
	required: ["id", "email", "farmId", "role", "status", "createdAt", "updatedAt"],
	additionalProperties: false,
};
