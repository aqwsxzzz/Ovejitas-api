import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	FlockEventParams,
	FlockEventDeleteParams,
	FlockEventCreate,
	FlockEventQuery,
	listFlockEventsSchema,
	createFlockEventSchema,
	deleteFlockEventSchema,
} from './flock-event.schema';
import { decodeId } from '../../utils/id-hash-util';
import { FlockEventSerializer } from './flock-event.serializer';
import { parsePagination } from '../../utils/pagination';

const flockEventRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	fastify.get('/flocks/:flockId/events', { schema: listFlockEventsSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FlockEventParams, Querystring: FlockEventQuery }>, reply) => {
		try {
			const { flockId } = request.params;
			const pagination = parsePagination(request.query);
			const result = await fastify.flockEventService.getFlockEvents(decodeId(flockId)!, pagination);
			const serialized = FlockEventSerializer.serializeMany(result.rows);
			reply.successWithPagination(serialized, result.pagination);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.post('/flocks/:flockId/events', { schema: createFlockEventSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FlockEventParams, Body: FlockEventCreate }>, reply) => {
		try {
			const { flockId } = request.params;
			const userId = request.user!.id;
			const event = await fastify.flockEventService.createFlockEvent({
				flockId: decodeId(flockId)!,
				data: request.body,
				userId,
			});
			const serialized = FlockEventSerializer.serialize(event);
			reply.success(serialized);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.delete('/flocks/:flockId/events/:id', { schema: deleteFlockEventSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FlockEventDeleteParams }>, reply) => {
		try {
			const { flockId, id } = request.params;
			await fastify.flockEventService.deleteFlockEvent({
				flockId: decodeId(flockId)!,
				eventId: decodeId(id)!,
			});
			reply.success(null);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default flockEventRoutes;
