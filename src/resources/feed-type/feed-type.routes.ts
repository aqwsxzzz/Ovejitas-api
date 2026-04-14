import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { ForeignKeyConstraintError } from 'sequelize';
import {
	FeedTypeCreate,
	FeedTypeUpdate,
	FeedTypeQuery,
	FeedTypeParams,
	listFeedTypesSchema,
	getFeedTypeByIdSchema,
	createFeedTypeSchema,
	updateFeedTypeSchema,
	deleteFeedTypeSchema,
} from './feed-type.schema';
import { FeedTypeSerializer } from './feed-type.serializer';
import { decodeId } from '../../utils/id-hash-util';
import { parsePagination } from '../../utils/pagination';

const feedTypeRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	fastify.get('/', { schema: listFeedTypesSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Querystring: FeedTypeQuery }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const pagination = parsePagination(request.query);
			const result = await fastify.feedTypeService.getFeedTypes(farmId, pagination);
			reply.successWithPagination(FeedTypeSerializer.serializeMany(result.rows), result.pagination);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/:id', { schema: getFeedTypeByIdSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FeedTypeParams }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const feedTypeId = decodeId(request.params.id);
			if (!feedTypeId) {
				return reply.error('Invalid feed type ID', 400);
			}

			const feedType = await fastify.feedTypeService.getFeedTypeById(feedTypeId, farmId);
			if (!feedType) {
				return reply.error('Feed type not found', 404);
			}

			reply.success(FeedTypeSerializer.serialize(feedType));
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.post('/', { schema: createFeedTypeSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Body: FeedTypeCreate }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const feedType = await fastify.feedTypeService.createFeedType(farmId, request.body);
			reply.success(FeedTypeSerializer.serialize(feedType));
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.put('/:id', { schema: updateFeedTypeSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FeedTypeParams; Body: FeedTypeUpdate }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const feedTypeId = decodeId(request.params.id);
			if (!feedTypeId) {
				return reply.error('Invalid feed type ID', 400);
			}

			const feedType = await fastify.feedTypeService.updateFeedType(feedTypeId, farmId, request.body);
			if (!feedType) {
				return reply.error('Feed type not found', 404);
			}

			reply.success(FeedTypeSerializer.serialize(feedType));
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.delete('/:id', { schema: deleteFeedTypeSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FeedTypeParams }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const feedTypeId = decodeId(request.params.id);
			if (!feedTypeId) {
				return reply.error('Invalid feed type ID', 400);
			}

			const deleted = await fastify.feedTypeService.deleteFeedType(feedTypeId, farmId);
			if (!deleted) {
				return reply.error('Feed type not found', 404);
			}

			reply.success(null, 'Feed type deleted successfully');
		} catch (error) {
			if (error instanceof ForeignKeyConstraintError) {
				return reply.error('This feed type has lots or consumption history and cannot be deleted', 409);
			}
			fastify.handleDbError(error, reply);
		}
	});
};

export default feedTypeRoutes;
