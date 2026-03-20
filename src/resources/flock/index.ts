import { FastifyPluginAsync } from 'fastify';
import flockRoutes from './flock.routes';

const flockPlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(flockRoutes, { prefix: '/flocks' });
};

export default flockPlugin;
