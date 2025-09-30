import { encodeId } from '../../utils/id-hash-util';
import { FarmMemberWithUser, FarmMemberWithUserResponse, FarmMemberRole } from './farm-member.schema';
import { getEntityPermissions } from '../../utils/permission.serializer';

export class FarmMemberSerializer {
	static serialize(farmMember: FarmMemberWithUser, userRole?: FarmMemberRole): FarmMemberWithUserResponse {
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
			...(userRole && { permissions: getEntityPermissions('member', userRole) }),
		};
	}

	static serializeMany(farmMembers: FarmMemberWithUser[], userRole?: FarmMemberRole): FarmMemberWithUserResponse[] {
		return farmMembers.map(farmMember => this.serialize(farmMember, userRole));
	}
}
