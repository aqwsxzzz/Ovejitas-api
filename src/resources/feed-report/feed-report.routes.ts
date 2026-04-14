import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	CostByFlockQuery,
	CostByLotParams,
	costByFlockSchema,
	costByLotSchema,
} from './feed-report.schema';
import { decodeId } from '../../utils/id-hash-util';

const feedReportRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	fastify.get('/cost-by-flock', { schema: costByFlockSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Querystring: CostByFlockQuery }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const filters: { from?: string; to?: string; flockId?: number } = {};
			if (request.query.from) filters.from = request.query.from;
			if (request.query.to) filters.to = request.query.to;
			if (request.query.flockId) {
				const decoded = decodeId(request.query.flockId);
				if (!decoded) return reply.error('Invalid flock ID', 400);
				filters.flockId = decoded;
			}

			const result = await fastify.feedReportService.getCostByFlock(farmId, filters);
			reply.success(result);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/cost-by-lot/:lotId', { schema: costByLotSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: CostByLotParams }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const lotId = decodeId(request.params.lotId);
			if (!lotId) return reply.error('Invalid lot ID', 400);

			const result = await fastify.feedReportService.getCostByLot(farmId, lotId);
			if (!result) return reply.error('Feed lot not found', 404);

			reply.success(result);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default feedReportRoutes;
