import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { ForeignKeyConstraintError } from 'sequelize';
import {
	FeedLotCreate,
	FeedLotUpdate,
	FeedLotQuery,
	FeedLotParams,
	listFeedLotsSchema,
	getFeedLotByIdSchema,
	createFeedLotSchema,
	updateFeedLotSchema,
	deleteFeedLotSchema,
} from './feed-lot.schema';
import { FeedLotSerializer } from './feed-lot.serializer';
import { decodeId } from '../../utils/id-hash-util';
import { parsePagination } from '../../utils/pagination';

const feedLotRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	fastify.get('/', { schema: listFeedLotsSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Querystring: FeedLotQuery }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const pagination = parsePagination(request.query);

			const filters: { feedTypeId?: number; hasStock?: boolean } = {};
			if (request.query.feedTypeId) {
				const decoded = decodeId(request.query.feedTypeId);
				if (!decoded) {
					return reply.error('Invalid feed type ID', 400);
				}
				filters.feedTypeId = decoded;
			}
			if (request.query.hasStock !== undefined) {
				filters.hasStock = request.query.hasStock;
			}

			const result = await fastify.feedLotService.getFeedLots(farmId, filters, pagination);
			reply.successWithPagination(FeedLotSerializer.serializeMany(result.rows), result.pagination);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/:id', { schema: getFeedLotByIdSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FeedLotParams }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const lotId = decodeId(request.params.id);
			if (!lotId) {
				return reply.error('Invalid feed lot ID', 400);
			}

			const lot = await fastify.feedLotService.getFeedLotById(lotId, farmId);
			if (!lot) {
				return reply.error('Feed lot not found', 404);
			}

			reply.success(FeedLotSerializer.serialize(lot));
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.post('/', { schema: createFeedLotSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Body: FeedLotCreate }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const userId = request.user!.id;
			const lot = await fastify.feedLotService.createFeedLot(farmId, userId, request.body);
			reply.success(FeedLotSerializer.serialize(lot));
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.put('/:id', { schema: updateFeedLotSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FeedLotParams; Body: FeedLotUpdate }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const lotId = decodeId(request.params.id);
			if (!lotId) {
				return reply.error('Invalid feed lot ID', 400);
			}

			const lot = await fastify.feedLotService.updateFeedLot(lotId, farmId, request.body);
			if (!lot) {
				return reply.error('Feed lot not found', 404);
			}

			reply.success(FeedLotSerializer.serialize(lot));
		} catch (error) {
			if (error instanceof Error && error.name === 'LotImmutableError') {
				return reply.error(error.message, 422);
			}
			fastify.handleDbError(error, reply);
		}
	});

	fastify.delete('/:id', { schema: deleteFeedLotSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FeedLotParams }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const lotId = decodeId(request.params.id);
			if (!lotId) {
				return reply.error('Invalid feed lot ID', 400);
			}

			const deleted = await fastify.feedLotService.deleteFeedLot(lotId, farmId);
			if (!deleted) {
				return reply.error('Feed lot not found', 404);
			}

			reply.success(null, 'Feed lot deleted successfully');
		} catch (error) {
			if (error instanceof ForeignKeyConstraintError) {
				return reply.error('This feed lot has consumption history and cannot be deleted', 409);
			}
			fastify.handleDbError(error, reply);
		}
	});
};

export default feedLotRoutes;
