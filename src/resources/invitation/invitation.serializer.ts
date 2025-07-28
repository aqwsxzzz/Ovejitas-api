import { encodeId } from '../../utils/id-hash-util';
import { InvitationModel } from './invitation.model';
import { InvitationResponse } from './invitation.schema';

export class InvitationSerializer {
	static serialize(invitation: InvitationModel): InvitationResponse {
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

	static serializeMany(invitations: InvitationModel[]): InvitationResponse[] {
		return invitations.map(invitation => this.serialize(invitation));
	}
}
