import { Database } from '../../database';
import { FarmMemberRole } from '../farm-member/farm-member.model';

export function isFarmMemberRole(role: FarmMemberRole): role is FarmMemberRole {
	return role === 'owner' || role === 'member';
}

export async function isAlreadyMemberOrInvited(email: string, farmId: number, db: Database) {
	const user = await db.models.User.findOne({ where: { email } });
	if (user) {
		const member = await db.models.FarmMember.findOne({ where: { userId: user.dataValues.id, farmId } });
		if (member) return { alreadyMember: true };
	}
	const invitation = await db.models.FarmInvitation.findOne({ where: { email, farmId, status: 'pending' } });
	if (invitation) return { alreadyInvited: true };
	return {};
}

export async function getUserFarmCount(userId: number, db: Database) {
	return await db.models.FarmMember.count({ where: { userId } });
}
