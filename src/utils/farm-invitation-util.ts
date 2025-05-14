import { User } from "../models/user-model";
import { FarmMembers } from "../models/farm-members-model";
import { FarmInvitation } from "../models/farm-invitation-model";
import { FarmMemberRole } from "../types/farm-members-types";

export function isFarmMemberRole(role: any): role is FarmMemberRole {
	return role === "owner" || role === "member";
}

export async function isAlreadyMemberOrInvited(email: string, farmId: number) {
	const user = await User.findOne({ where: { email } });
	if (user) {
		const member = await FarmMembers.findOne({ where: { userId: user.id, farmId } });
		if (member) return { alreadyMember: true };
	}
	const invitation = await FarmInvitation.findOne({ where: { email, farmId, status: "pending" } });
	if (invitation) return { alreadyInvited: true };
	return {};
}

export async function getUserFarmCount(userId: number) {
	return await FarmMembers.count({ where: { userId } });
}
