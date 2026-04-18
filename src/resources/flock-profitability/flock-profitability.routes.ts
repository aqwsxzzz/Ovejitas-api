import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { decodeId } from '../../utils/id-hash-util';
import {
	FlockProfitabilityQuery,
	flockProfitabilitySchema,
} from './flock-profitability.schema';

const MAX_RANGE_DAYS = 730;

const flockProfitabilityRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {
	fastify.get('/', {
		schema: flockProfitabilitySchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Querystring: FlockProfitabilityQuery }>, reply) => {
		const farmId = request.lastVisitedFarmId;
		const { period, from, to, flockId: flockIdParam } = request.query;

		if (from > to) {
			return reply.error('Query parameter "to" must be on or after "from".', 400);
		}
		if (daysBetween(from, to) > MAX_RANGE_DAYS) {
			return reply.error(`Date range exceeds maximum of ${MAX_RANGE_DAYS} days.`, 400);
		}

		let flockId: number | undefined;
		if (flockIdParam) {
			const decoded = decodeId(flockIdParam);
			if (!decoded) {
				return reply.error('Invalid flock ID', 400);
			}
			flockId = decoded;
		}

		try {
			const report = await fastify.flockProfitabilityService.getReport({
				farmId,
				period,
				from,
				to,
				flockId,
			});
			return reply.success(report);
		} catch (error) {
			if (error instanceof Error && error.name === 'EggPricingMissingError') {
				return reply.error(error.message, 422);
			}
			throw error;
		}
	});
};

function daysBetween(from: string, to: string): number {
	const fromMs = new Date(`${from}T00:00:00Z`).getTime();
	const toMs = new Date(`${to}T00:00:00Z`).getTime();
	return Math.round((toMs - fromMs) / 86_400_000);
}

export default flockProfitabilityRoutes;
