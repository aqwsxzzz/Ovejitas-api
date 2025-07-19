import { Database } from '../../database';
import { decodeId } from '../../utils/id-hash-util';
import { createInvitationToken } from '../../utils/token-util';
import { FarmMemberRole } from '../farm-member/farm-member.model';
import { isAlreadyMemberOrInvited } from './invitation.helper';
import { FarmInvitationStatus } from './invitation.model';
import { InvitationCreateInput } from './invitation.schema';

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
			const farmCount = await this.db.models.FarmMember.count({ where: { userId: user.dataValues.id } });
			if (farmCount >= MAX_FREE_USER_FARMS) {
				throw new Error('User has reached the maximum number of farm memberships');
			}
		}

		const token = createInvitationToken();
		const expiresAt = new Date(Date.now() + INVITATION_EXPIRY_DAYS * 24 * 60 * 60 * 1000);

		const invitation = await this.db.models.FarmInvitation.create({
			email, farmId: decodedFarmId!, token, role: 'member' as FarmMemberRole, status: 'pending' as FarmInvitationStatus, expiresAt: expiresAt.toDateString(),
		});

		return invitation;

	}

}
