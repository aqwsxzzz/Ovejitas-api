import { FastifyPluginAsync } from 'fastify';
import speciesRoutes from './species.routes';

const speciesPlugin: FastifyPluginAsync = async (fastify) => {
	fastify.register(speciesRoutes, { prefix: '/species' });
};

export default speciesPlugin;
