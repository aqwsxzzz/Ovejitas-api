import { BaseService } from '../../services/base.service';
import { FarmMemberModel } from './farm-member.model';
import { FarmMemberCreateInput, FarmMemberWithUser } from './farm-member.schema';

export class FarmMemberService extends BaseService {

	async createFarmMember(data: FarmMemberCreateInput): Promise<FarmMemberModel> {
		const farmMember = await this.db.models.FarmMember.create(data);
		return farmMember;
	}

	async getFarmMembersWithUsers(farmId: number): Promise<FarmMemberWithUser[]> {
		const farmMembers = await this.db.models.FarmMember.findAll({
			where: { farmId },
			include: [{
				model: this.db.models.User,
				as: 'user',
				attributes: ['id', 'displayName', 'email'],
			}],
		});
		return farmMembers as unknown as FarmMemberWithUser[];
	}
}
