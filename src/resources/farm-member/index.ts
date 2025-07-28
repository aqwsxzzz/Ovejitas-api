import { FastifyPluginAsync } from 'fastify';
import farmMemberRoutes from './farm-member.routes';

const farmMemberPlugin: FastifyPluginAsync = async (fastify) => {
	fastify.register(farmMemberRoutes, { prefix: '/farm-members' });
};

export default farmMemberPlugin;
