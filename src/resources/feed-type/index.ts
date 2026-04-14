import { FastifyPluginAsync } from 'fastify';
import feedTypeRoutes from './feed-type.routes';

const feedTypePlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(feedTypeRoutes, { prefix: '/feed-types' });
};

export default feedTypePlugin;
