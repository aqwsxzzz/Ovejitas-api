import { Database } from '../../database';
import { decodeId } from '../../utils/id-hash-util';
import { hashPassword } from '../../utils/password-util';
import { createInvitationToken } from '../../utils/token-util';
import { FarmMemberRole } from '../farm-member/farm-member.model';
import { UserLanguage } from '../user/user.schema';
import { getUserFarmCount, isAlreadyMemberOrInvited } from './invitation.helper';
import { InvitationStatus, InvitationAcceptInput, InvitationCreateInput, ListInvitationParams } from './invitation.schema';

const MAX_FREE_USER_FARMS = 2;
const INVITATION_EXPIRY_DAYS = 7;

export class InvitationService {
	private db: Database;

	constructor(db: Database) {
		this.db = db;
	}

	 async createInvitation(data: InvitationCreateInput) {
		const { email, farmId } = data;
		const decodedFarmId = decodeId(farmId);

		const { alreadyInvited, alreadyMember } = await isAlreadyMemberOrInvited(email, decodedFarmId!, this.db);

		if (alreadyMember) {
			throw new Error('User is already a member of this farm');
		}
		if (alreadyInvited) {
			throw new Error('User is already invited to this farm');
		}

		const user = await this.db.models.User.findOne({ where: { email } });
		if (user) {
			const farmCount = await getUserFarmCount(user.dataValues.id, this.db);
			if (farmCount >= MAX_FREE_USER_FARMS) {
				throw new Error('User has reached the maximum number of farm memberships');
			}
		}

		const token = createInvitationToken();
		const expiresAt = new Date(Date.now() + INVITATION_EXPIRY_DAYS * 24 * 60 * 60 * 1000);

		const invitation = await this.db.models.Invitation.create({
			email, farmId: decodedFarmId!, token, role: 'member' as FarmMemberRole, status: InvitationStatus.PENDING, expiresAt: expiresAt.toDateString(),
		});

		return invitation;

	 }

	// Accept Invitation
	async acceptInvitation(data: InvitationAcceptInput) {

		const { token, password, displayName, language } = data;
		const invitation = await this.db.models.Invitation.findOne({ where: { token, status: 'pending' } });

		if (!invitation) throw new Error('Invalid or expired invitation token');

		if (!invitation.dataValues.farmId) throw new Error('Invalid farm ID');

		if (!invitation.dataValues.expiresAt || new Date(invitation.dataValues.expiresAt).getTime() < Date.now()) {
			invitation.setDataValue('status', InvitationStatus.EXPIRED);
			await invitation.save();
			return invitation;
		}

		let user = await this.db.models.User.findOne({ where: { email: invitation.dataValues.email } });

		if (!user) {
			const hashedPassword = await hashPassword(password);
			user = await this.db.models.User.create({
				displayName,
				email: invitation.dataValues.email,
				password: hashedPassword,
				language: (language as UserLanguage) || UserLanguage.ES,
				lastVisitedFarmId: Number(invitation.dataValues.farmId),
			});
		}
		const farmCount = await getUserFarmCount(user.dataValues.id, this.db);

		if (farmCount >= MAX_FREE_USER_FARMS) {
			throw new Error('You have reached the maximum number of farm memberships');
		}

		await this.db.models.FarmMember.create({
			farmId: Number(invitation.dataValues.farmId),
			userId: user.dataValues.id,
			role: invitation.dataValues.role,
		});

		invitation.setDataValue('status', InvitationStatus.ACCEPTED);
		return await invitation.save();

	}

	// List Invitations
	async listInvitations(data: ListInvitationParams) {
		const { farmId } = data;
		const decodedFarmId = decodeId(farmId);

		if (typeof decodedFarmId !== 'number') throw new Error('Invalid farm ID');

		const invitations = await this.db.models.Invitation.findAll({
			where: { farmId: String(decodedFarmId), status: InvitationStatus.PENDING },
		});

		return invitations;
	}

}
