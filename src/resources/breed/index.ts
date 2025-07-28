import { FastifyPluginAsync } from 'fastify';
import breedRoutes from './breed.routes';

const breedPlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(breedRoutes, { prefix: '/breeds' });
};

export default breedPlugin;
