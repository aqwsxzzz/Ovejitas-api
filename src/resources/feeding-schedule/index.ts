import { FastifyPluginAsync } from 'fastify';
import feedingScheduleRoutes from './feeding-schedule.routes';

const feedingSchedulePlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(feedingScheduleRoutes, { prefix: '/feeding-schedules' });
};

export default feedingSchedulePlugin;
