import { FastifyPluginAsync } from 'fastify';
import userRoutes from './user.routes';

const userPlugin: FastifyPluginAsync = async (fastify) => {
	fastify.register(userRoutes, { prefix: '/users' });
};

export default userPlugin;
