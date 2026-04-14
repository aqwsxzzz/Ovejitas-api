import { FastifyPluginAsync } from 'fastify';
import feedConsumptionRoutes from './feed-consumption.routes';
import logTodaysFeedingRoutes from './log-todays-feeding.routes';

const feedConsumptionPlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(feedConsumptionRoutes, { prefix: '/feed-consumptions' });
	await fastify.register(logTodaysFeedingRoutes);
};

export default feedConsumptionPlugin;
