import { FastifyPluginAsync } from 'fastify';
import feedConsumptionRoutes from './feed-consumption.routes';

const feedConsumptionPlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(feedConsumptionRoutes, { prefix: '/feed-consumptions' });
};

export default feedConsumptionPlugin;
