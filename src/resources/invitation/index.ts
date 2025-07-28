import { FastifyPluginAsync } from 'fastify';
import invitationRoutes from './invitation.routes';

const invitationPlugin: FastifyPluginAsync = async (fastify) => {
	fastify.register(invitationRoutes, { prefix: '/invitations' });
};

export default invitationPlugin;
