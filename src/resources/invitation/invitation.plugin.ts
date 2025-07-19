import { FastifyPluginAsync } from 'fastify';
import { createInvitationSchema, InvitationCreateInput, invitationSchemas } from './invitation.schema';
import { InvitationService } from './invitation.service';
import { InvitationSerializer } from './invitation.serializer';

const invitationPlugin: FastifyPluginAsync = async (fastify) => {
	invitationSchemas.forEach(schema => fastify.addSchema(schema));

	const invitationService = new InvitationService(fastify.db);

	fastify.post('/invitations', { schema: createInvitationSchema }, async (request, reply) => {
		try {
			const data = request.body as InvitationCreateInput;
			const invitation = await invitationService.createInvitation(data);
			const serializedInvitation = InvitationSerializer.serialize(invitation);
			reply.success(serializedInvitation);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

};

export default invitationPlugin;
