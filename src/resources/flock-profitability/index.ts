import { FastifyPluginAsync } from 'fastify';
import flockProfitabilityRoutes from './flock-profitability.routes';

const flockProfitabilityPlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(flockProfitabilityRoutes, { prefix: '/reports/flock-profitability' });
};

export default flockProfitabilityPlugin;
