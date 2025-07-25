import { FastifyPluginAsync } from 'fastify';
import farmRoutes from './farm.routes';

const farmPlugin: FastifyPluginAsync = async (fastify) => {
	fastify.register(farmRoutes, { prefix: '/farms' });
};

export default farmPlugin;
