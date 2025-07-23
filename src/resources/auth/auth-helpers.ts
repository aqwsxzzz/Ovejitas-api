
import { Transaction } from 'sequelize';
import { UserSignupInput } from './auth.schema';
import { Database } from '../../database';
import { hashPassword } from '../../utils/password-util';
import { UserLanguage } from '../user/user.schema';
import {  InvitationStatus } from '../invitation/invitation.schema';
import { FarmMemberRole } from '../farm-member/farm-member.schema';

export async function handleInvitationSignUp(body: UserSignupInput, db: Database, transaction: Transaction) {
	const { displayName, email, password, language = 'es', invitationToken } = body;
	const invitation = await db.models.Invitation.findOne({ where: { token: invitationToken, status: 'pending' }, transaction });

	if (!invitation) {
		throw new Error('Invalid or expired invitation token');
	}

	if (!invitation.dataValues.expiresAt || new Date(invitation.dataValues.expiresAt).getTime() < Date.now()) {
		invitation.setDataValue('status', InvitationStatus.EXPIRED);
		await invitation.save({ transaction });
		throw new Error('Invitation has expired');
	}
	const hashedPassword = await hashPassword(password);
	const user = await db.models.User.create({ displayName, email: email.toLowerCase(), password: hashedPassword, language: language as UserLanguage }, { transaction });

	await db.models.FarmMember.create({ farmId: (invitation.dataValues.farmId)!, userId: user.dataValues.id, role: invitation.dataValues.role }, { transaction });
	user.set('lastVisitedFarmId', (invitation.dataValues.farmId));
	await user.save({ transaction });
	invitation.setDataValue('status', InvitationStatus.ACCEPTED);
	await invitation.save({ transaction });
	return user;
}

export async function handleDefaultSignUp(body: UserSignupInput, db:Database, transaction: Transaction) {
	const { displayName, email, password, language = 'es' } = body;

	const hashedPassword = await hashPassword(password);

	const user = await db.models.User.create({ displayName, email: email.toLowerCase(), password: hashedPassword, language: language as UserLanguage }, { transaction });

	const farmName = language === 'en' ? 'My farm' : 'Mi Granja';

	const farm = await db.models.Farm.create({ name: farmName }, { transaction });

	await db.models.FarmMember.create({ farmId: farm.dataValues.id, userId: user.dataValues.id, role: FarmMemberRole.OWNER }, { transaction });

	user.setDataValue('lastVisitedFarmId', farm.dataValues.id);

	await user.save({ transaction });

	return user;
}
