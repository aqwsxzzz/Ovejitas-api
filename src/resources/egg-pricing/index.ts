import { FastifyPluginAsync } from 'fastify';
import eggPricingRoutes from './egg-pricing.routes';

const eggPricingPlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(eggPricingRoutes, { prefix: '/egg-pricings' });
};

export default eggPricingPlugin;
