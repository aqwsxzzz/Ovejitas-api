import { FastifyPluginAsync } from 'fastify';
import flockEventRoutes from './flock-event.routes';

const flockEventPlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(flockEventRoutes);
};

export default flockEventPlugin;
