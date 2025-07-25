import { FastifyPluginAsync, FastifyRequest } from 'fastify';
import { createInvitationSchema, InvitationAcceptInput, InvitationCreateInput,  ListInvitationParams, listInvitationsSchema } from './invitation.schema';
import { InvitationService } from './invitation.service';
import { InvitationSerializer } from './invitation.serializer';

const invitationPlugin: FastifyPluginAsync = async (fastify) => {

	const invitationService = new InvitationService(fastify.db);

	// Create Invitation
	fastify.post('/invitations', { schema: createInvitationSchema }, async (request: FastifyRequest<{ Body: InvitationCreateInput }>, reply) => {
		try {
			const data = request.body;
			const invitation = await invitationService.createInvitation(data);
			const serializedInvitation = InvitationSerializer.serialize(invitation);
			reply.success(serializedInvitation);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// Accept Invitation
	fastify.post('/invitations/accept', { schema: createInvitationSchema }, async (request: FastifyRequest<{ Body: InvitationAcceptInput }>, reply) => {
		try {
			const data = request.body;
			const invitation = await invitationService.acceptInvitation(data);
			const serializedInvitation = InvitationSerializer.serialize(invitation);
			reply.success(serializedInvitation);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// List Invitations
	fastify.get('/invitations', { schema: listInvitationsSchema }, async (request: FastifyRequest<{ Params: ListInvitationParams }>, reply) => {
		try {
			const data = request.params;
			const invitations = await invitationService.listInvitations(data);
			const serializedInvitations = InvitationSerializer.serializeMany(invitations);
			reply.success(serializedInvitations);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

};

export default invitationPlugin;
