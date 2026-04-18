import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	EggPricingCreate,
	createEggPricingSchema,
	getActiveEggPricingSchema,
	getEggPricingHistorySchema,
} from './egg-pricing.schema';
import { EggPricingSerializer } from './egg-pricing.serializer';

const eggPricingRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {
	async function getFarmCurrency(farmId: number): Promise<string | null> {
		const farm = await fastify.db.models.Farm.findByPk(farmId, { attributes: ['currency'] });
		return farm?.currency ?? null;
	}

	fastify.get('/active', { schema: getActiveEggPricingSchema, preHandler: fastify.authenticate }, async (request, reply) => {
		const farmId = request.lastVisitedFarmId;
		const pricing = await fastify.eggPricingService.getActive(farmId);
		if (!pricing) {
			return reply.error('Egg pricing not configured for this farm', 404);
		}
		const currency = await getFarmCurrency(farmId);
		return reply.success(EggPricingSerializer.serialize(pricing, currency));
	});

	fastify.get('/history', { schema: getEggPricingHistorySchema, preHandler: fastify.authenticate }, async (request, reply) => {
		const farmId = request.lastVisitedFarmId;
		const [rows, currency] = await Promise.all([
			fastify.eggPricingService.getHistory(farmId),
			getFarmCurrency(farmId),
		]);
		return reply.success(EggPricingSerializer.serializeMany(rows, currency));
	});

	fastify.post('/', { schema: createEggPricingSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Body: EggPricingCreate }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const effectiveFrom = request.body.effectiveFrom ?? new Date().toISOString().slice(0, 10);
			const pricing = await fastify.eggPricingService.setPrice(farmId, request.body.pricePerEgg, effectiveFrom);
			const currency = await getFarmCurrency(farmId);
			return reply.created(EggPricingSerializer.serialize(pricing, currency));
		} catch (error) {
			if (error instanceof Error && error.name === 'EggPricingOrderingError') {
				return reply.error(error.message, 409);
			}
			throw error;
		}
	});
};

export default eggPricingRoutes;
