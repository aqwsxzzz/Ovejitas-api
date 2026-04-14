import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	FeedingScheduleCreate,
	FeedingScheduleUpdate,
	FeedingScheduleQuery,
	FeedingScheduleParams,
	listFeedingSchedulesSchema,
	getFeedingScheduleByIdSchema,
	createFeedingScheduleSchema,
	updateFeedingScheduleSchema,
	deleteFeedingScheduleSchema,
} from './feeding-schedule.schema';
import { FeedingScheduleSerializer } from './feeding-schedule.serializer';
import { FeedingScheduleFilters } from './feeding-schedule.service';
import { decodeId } from '../../utils/id-hash-util';
import { parsePagination } from '../../utils/pagination';

const feedingScheduleRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	fastify.get('/', { schema: listFeedingSchedulesSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Querystring: FeedingScheduleQuery }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const pagination = parsePagination(request.query);

			const filters: FeedingScheduleFilters = {};
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
			if (request.query.activeOnly !== undefined) filters.activeOnly = request.query.activeOnly;

			const result = await fastify.feedingScheduleService.getFeedingSchedules(farmId, filters, pagination);
			reply.successWithPagination(FeedingScheduleSerializer.serializeMany(result.rows), result.pagination);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/:id', { schema: getFeedingScheduleByIdSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FeedingScheduleParams }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const scheduleId = decodeId(request.params.id);
			if (!scheduleId) return reply.error('Invalid schedule ID', 400);

			const schedule = await fastify.feedingScheduleService.getFeedingScheduleById(scheduleId, farmId);
			if (!schedule) return reply.error('Feeding schedule not found', 404);

			reply.success(FeedingScheduleSerializer.serialize(schedule));
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.post('/', { schema: createFeedingScheduleSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Body: FeedingScheduleCreate }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const schedule = await fastify.feedingScheduleService.createFeedingSchedule(farmId, request.body);
			reply.success(FeedingScheduleSerializer.serialize(schedule));
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.put('/:id', { schema: updateFeedingScheduleSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FeedingScheduleParams; Body: FeedingScheduleUpdate }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const scheduleId = decodeId(request.params.id);
			if (!scheduleId) return reply.error('Invalid schedule ID', 400);

			const schedule = await fastify.feedingScheduleService.updateFeedingSchedule(scheduleId, farmId, request.body);
			if (!schedule) return reply.error('Feeding schedule not found', 404);

			reply.success(FeedingScheduleSerializer.serialize(schedule));
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.delete('/:id', { schema: deleteFeedingScheduleSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FeedingScheduleParams }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const scheduleId = decodeId(request.params.id);
			if (!scheduleId) return reply.error('Invalid schedule ID', 400);

			const deleted = await fastify.feedingScheduleService.deleteFeedingSchedule(scheduleId, farmId);
			if (!deleted) return reply.error('Feeding schedule not found', 404);

			reply.success(null, 'Feeding schedule deleted successfully');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default feedingScheduleRoutes;
