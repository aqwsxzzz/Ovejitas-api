import { FastifyPluginAsync } from 'fastify';
import feedReportRoutes from './feed-report.routes';

const feedReportPlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(feedReportRoutes, { prefix: '/feed-reports' });
};

export default feedReportPlugin;
