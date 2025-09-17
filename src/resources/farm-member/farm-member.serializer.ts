import { encodeId } from '../../utils/id-hash-util';
import { FarmMemberWithUser, FarmMemberWithUserResponse } from './farm-member.schema';

export class FarmMemberSerializer {
	static serialize(farmMember: FarmMemberWithUser): FarmMemberWithUserResponse {
		return {
			id: encodeId(farmMember.dataValues.id),
			farmId: encodeId(farmMember.dataValues.farmId),
			userId: encodeId(farmMember.dataValues.userId),
			role: farmMember.dataValues.role,
			user: {
				id: encodeId(farmMember.user.id),
				displayName: farmMember.user.displayName,
				email: farmMember.user.email,
			},
			createdAt: farmMember.dataValues.createdAt,
			updatedAt: farmMember.dataValues.updatedAt,
		};
	}

	static serializeMany(farmMembers: FarmMemberWithUser[]): FarmMemberWithUserResponse[] {
		return farmMembers.map(farmMember => this.serialize(farmMember));
	}
}