import { FastifyPluginAsync } from 'fastify';
import animalRoutes from './animal.routes';

const animalPlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(animalRoutes, { prefix: '/animals' });
};

export default animalPlugin;
