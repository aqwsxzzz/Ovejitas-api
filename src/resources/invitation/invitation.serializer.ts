import { encodeId } from '../../utils/id-hash-util';
import { FarmInvitationModel } from './invitation.model';
import { InvitationResponse } from './invitation.schema';

export class InvitationSerializer {
	static serialize(invitation: FarmInvitationModel): InvitationResponse {
		return {
			id: encodeId(invitation.dataValues.id!),
			email: invitation.dataValues.email,
			farmId: encodeId(invitation.dataValues.farmId!),
			role: invitation.dataValues.role,
			status: invitation.dataValues.status,
			token: invitation.dataValues.token,
			createdAt: invitation.dataValues.createdAt,
			expiresAt: invitation.dataValues.expiresAt,
			updatedAt: invitation.dataValues.updatedAt,
		};
	}
}
