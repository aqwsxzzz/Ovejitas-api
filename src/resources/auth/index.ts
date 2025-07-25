import { FastifyPluginAsync } from 'fastify';
import authRoutes from './auth.routes';

const authPlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(authRoutes, { prefix: '/auth' });
};

export default authPlugin;
