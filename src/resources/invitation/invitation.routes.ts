import { FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	acceptInvitationSchema,
	createInvitationSchema,
	InvitationAcceptInput,
	InvitationCreateInput,
	ListInvitationParams,
	listInvitationsSchema,
} from './invitation.schema';
import { InvitationSerializer } from './invitation.serializer';
import { parsePagination } from '../../utils/pagination';

const invitationRoutes: FastifyPluginAsync = async (fastify) => {
	// Create Invitation
	fastify.post('/', {
		schema: createInvitationSchema,
	}, async (request: FastifyRequest<{ Body: InvitationCreateInput }>, reply) => {
		try {
			const data = request.body;
			const invitation = await fastify.invitationService.createInvitation(data);
			const serializedInvitation = InvitationSerializer.serialize(invitation);
			reply.success(serializedInvitation);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// Accept Invitation
	fastify.post('/accept', {
		schema: acceptInvitationSchema,
	}, async (request: FastifyRequest<{ Body: InvitationAcceptInput }>, reply) => {
		try {
			const data = request.body;
			const invitation = await fastify.invitationService.acceptInvitation(data);
			const serializedInvitation = InvitationSerializer.serialize(invitation);
			reply.success(serializedInvitation);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// List Invitations
	fastify.get('/', {
		schema: listInvitationsSchema,
	}, async (request: FastifyRequest<{ Querystring: ListInvitationParams }>, reply) => {
		try {
			const data = request.query;
			const pagination = parsePagination(request.query);
			const result = await fastify.invitationService.listInvitations(data, pagination ?? undefined);

			if (pagination && !Array.isArray(result)) {
				const serializedInvitations = InvitationSerializer.serializeMany(result.rows);
				return reply.successWithPagination(serializedInvitations, result.pagination);
			}

			const invitations = Array.isArray(result) ? result : result.rows;
			const serializedInvitations = InvitationSerializer.serializeMany(invitations);
			reply.success(serializedInvitations);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default invitationRoutes;
