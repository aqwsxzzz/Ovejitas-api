import { User, UserRole } from "../models/user-model";
import { encodeId } from "../utils/id-hash-util";

export const userResponseSchema = {
	type: "object",
	properties: {
		id: { type: "string" },
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

export function serializeUser(user: User) {
	return {
		id: encodeId(user.id),
		displayName: user.displayName,
		email: user.email,
		isActive: user.isActive,
		role: user.role,
		createdAt: user.createdAt,
		updatedAt: user.updatedAt,
	};
}
