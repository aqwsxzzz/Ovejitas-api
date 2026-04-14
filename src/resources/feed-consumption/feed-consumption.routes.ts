import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	FeedConsumptionCreate,
	FeedConsumptionQuery,
	FeedConsumptionParams,
	listFeedConsumptionsSchema,
	getFeedConsumptionByIdSchema,
	createFeedConsumptionSchema,
	deleteFeedConsumptionSchema,
} from './feed-consumption.schema';
import { FeedConsumptionSerializer } from './feed-consumption.serializer';
import { FeedConsumptionFilters, FeedConsumptionWithLots } from './feed-consumption.service';
import { decodeId } from '../../utils/id-hash-util';
import { parsePagination } from '../../utils/pagination';

const feedConsumptionRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	fastify.get('/', { schema: listFeedConsumptionsSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Querystring: FeedConsumptionQuery }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const pagination = parsePagination(request.query);

			const filters: FeedConsumptionFilters = {};
			if (request.query.flockId) {
				const decoded = decodeId(request.query.flockId);
				if (!decoded) return reply.error('Invalid flock ID', 400);
				filters.flockId = decoded;
			}
			if (request.query.feedTypeId) {
				const decoded = decodeId(request.query.feedTypeId);
				if (!decoded) return reply.error('Invalid feed type ID', 400);
				filters.feedTypeId = decoded;
			}
			if (request.query.from) filters.from = request.query.from;
			if (request.query.to) filters.to = request.query.to;

			const includeLots = request.query.include?.includes('lots') ?? false;
			const result = await fastify.feedConsumptionService.getFeedConsumptions(farmId, filters, includeLots, pagination);
			const serialized = FeedConsumptionSerializer.serializeMany(result.rows as FeedConsumptionWithLots[]);
			reply.successWithPagination(serialized, result.pagination);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/:id', { schema: getFeedConsumptionByIdSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FeedConsumptionParams }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const consumptionId = decodeId(request.params.id);
			if (!consumptionId) {
				return reply.error('Invalid consumption ID', 400);
			}

			const consumption = await fastify.feedConsumptionService.getFeedConsumptionById(consumptionId, farmId);
			if (!consumption) {
				return reply.error('Feed consumption not found', 404);
			}

			reply.success(FeedConsumptionSerializer.serialize(consumption as FeedConsumptionWithLots));
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.post('/', { schema: createFeedConsumptionSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Body: FeedConsumptionCreate }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const userId = request.user!.id;
			const consumption = await fastify.feedConsumptionService.createFeedConsumption(farmId, userId, request.body);
			reply.success(FeedConsumptionSerializer.serialize(consumption as FeedConsumptionWithLots));
		} catch (error) {
			if (error instanceof Error && error.name === 'InsufficientStockError') {
				return reply.error(error.message, 422);
			}
			fastify.handleDbError(error, reply);
		}
	});

	fastify.delete('/:id', { schema: deleteFeedConsumptionSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FeedConsumptionParams }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const consumptionId = decodeId(request.params.id);
			if (!consumptionId) {
				return reply.error('Invalid consumption ID', 400);
			}

			const deleted = await fastify.feedConsumptionService.deleteFeedConsumption(consumptionId, farmId);
			if (!deleted) {
				return reply.error('Feed consumption not found', 404);
			}

			reply.success(null, 'Feed consumption deleted successfully');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default feedConsumptionRoutes;
