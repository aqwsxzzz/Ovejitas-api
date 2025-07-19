import { Database } from '../../database';

export async function isAlreadyMemberOrInvited(email: string, farmId: number, db: Database) {
	const user = await db.models.User.findOne({ where: { email } });
	if (user) {
		const member = await db.models.FarmMember.findOne({ where: { userId: user.dataValues.id, farmId } });
		if (member) return { alreadyMember: true };
	}
	const invitation = await db.models.Invitation.findOne({ where: { email, farmId, status: 'pending' } });
	if (invitation) return { alreadyInvited: true };
	return {};
}

export async function getUserFarmCount(userId: number, db: Database) {
	return await db.models.FarmMember.count({ where: { userId } });
}
