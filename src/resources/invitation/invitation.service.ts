import { FindOptions } from 'sequelize';
import { BaseService } from '../../services/base.service';
import { decodeId } from '../../utils/id-hash-util';
import { createInvitationToken } from '../../utils/token-util';
import { FarmMemberRole } from '../farm-member/farm-member.schema';
import { InvitationStatus, InvitationAcceptInput, InvitationCreateInput, ListInvitationParams } from './invitation.schema';
import { FilterConfig, FilterConfigBuilder } from '../../utils/filter-parser';

const MAX_FREE_USER_FARMS = 2;
const INVITATION_EXPIRY_DAYS = 7;

export class InvitationService extends BaseService {

	private static readonly ALLOWED_FILTERS: FilterConfig = {
		status: FilterConfigBuilder.enum('status', Object.values(InvitationStatus)),
		email: FilterConfigBuilder.string('email', 'ilike'),

	};

	 async createInvitation(data: InvitationCreateInput) {
		const { email, farmId } = data;
		const decodedFarmId = decodeId(farmId);

		const { alreadyInvited, alreadyMember } = await this.isAlreadyMemberOrInvited(email, decodedFarmId! );

		if (alreadyMember) {
			throw new Error('User is already a member of this farm');
		}
		if (alreadyInvited) {
			throw new Error('User is already invited to this farm');
		}

		const user = await this.db.models.User.findOne({ where: { email } });
		if (user) {
			const farmCount = await this.getUserFarmCount(user.dataValues.id);
			if (farmCount >= MAX_FREE_USER_FARMS) {
				throw new Error('User has reached the maximum number of farm memberships');
			}
		}

		const token = createInvitationToken();
		const expiresAt = new Date(Date.now() + INVITATION_EXPIRY_DAYS * 24 * 60 * 60 * 1000);

		const invitation = await this.db.models.Invitation.create({
			email, farmId: decodedFarmId!, token, role: FarmMemberRole.MEMBER, status: InvitationStatus.PENDING, expiresAt: expiresAt.toDateString(),
		});

		return invitation;

	 }

	// Accept Invitation
	async acceptInvitation(data: InvitationAcceptInput) {

		const { token } = data;
		const invitation = await this.db.models.Invitation.findOne({ where: { token, status: 'pending' } });

		if (!invitation) throw new Error('Invalid or expired invitation token');

		if (!invitation.dataValues.farmId) throw new Error('Invalid farm ID');

		if (!invitation.dataValues.expiresAt || new Date(invitation.dataValues.expiresAt).getTime() < Date.now()) {
			invitation.setDataValue('status', InvitationStatus.EXPIRED);
			await invitation.save();
			return invitation;
		}

		const user = await this.db.models.User.findOne({ where: { email: invitation.dataValues.email } });

		if (!user) {
			throw new Error('User not found');
		}
		const farmCount = await this.getUserFarmCount(user.dataValues.id);

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
		const { farmId, status, email } = data;
		const decodedFarmId = decodeId(farmId!);

		if (typeof decodedFarmId !== 'number') throw new Error('Invalid farm ID');

		const filterWhere = this.parseFilters({ status: status ?? '', email: email ?? '' }, InvitationService.ALLOWED_FILTERS);

		// Combine base condition with filters
		const findOptions: FindOptions = {
			where: {
				farmId: decodedFarmId,
				...filterWhere,
			},
		};

		const invitations = await this.db.models.Invitation.findAll(findOptions);

		return invitations;
	}

	private  async  isAlreadyMemberOrInvited(email: string, farmId: number) {
		const user = await this.db.models.User.findOne({ where: { email } });
		if (user) {
			const member = await this.db.models.FarmMember.findOne({ where: { userId: user.dataValues.id, farmId } });
			if (member) return { alreadyMember: true };
		}
		const invitation = await this.db.models.Invitation.findOne({ where: { email, farmId, status: 'pending' } });
		if (invitation) return { alreadyInvited: true };
		return {};
	}

	private async  getUserFarmCount(userId: number  ) {
		return await this.db.models.FarmMember.count({ where: { userId } });
	}

}
