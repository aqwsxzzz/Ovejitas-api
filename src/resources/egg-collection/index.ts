import { FastifyPluginAsync } from 'fastify';
import eggCollectionRoutes from './egg-collection.routes';

const eggCollectionPlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(eggCollectionRoutes);
};

export default eggCollectionPlugin;
