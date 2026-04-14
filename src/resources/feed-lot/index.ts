import { FastifyPluginAsync } from 'fastify';
import feedLotRoutes from './feed-lot.routes';

const feedLotPlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(feedLotRoutes, { prefix: '/feed-lots' });
};

export default feedLotPlugin;
