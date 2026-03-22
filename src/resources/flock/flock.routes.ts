import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	FlockCreate,
	FlockUpdate,
	FlockInclude,
	FlockParams,
	createFlockSchema,
	listFlockSchema,
	getFlockByIdSchema,
	updateFlockSchema,
	deleteFlockSchema,
} from './flock.schema';
import { FlockSerializer } from './flock.serializer';
import { decodeId } from '../../utils/id-hash-util';
import { parsePagination } from '../../utils/pagination';

const flockRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	fastify.get('/', { schema: listFlockSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Querystring: FlockInclude }>, reply) => {
		try {
			const { include, language } = request.query;
			const farmId = request.lastVisitedFarmId;
			const filters = fastify.flockService.extractFilterParams(request.query);
			const pagination = parsePagination(request.query);
			const result = await fastify.flockService.getFlocks(farmId, language, include, filters, pagination);
			const serialized = FlockSerializer.serializeMany(result.rows);
			reply.successWithPagination(serialized, result.pagination);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/:id', { schema: getFlockByIdSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FlockParams, Querystring: FlockInclude }>, reply) => {
		try {
			const { id } = request.params;
			const { include, language } = request.query;
			const flockId = decodeId(id);

			if (!flockId) {
				return reply.error('Invalid flock ID', 400);
			}

			const flock = await fastify.flockService.getFlockById(flockId, language, include);

			if (!flock) {
				return reply.error('Flock not found', 404);
			}

			const serialized = FlockSerializer.serialize(flock);
			reply.success(serialized);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.post('/', { schema: createFlockSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Body: FlockCreate }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const { language } = request.body;
			const flock = await fastify.flockService.createFlock({ data: { ...request.body, farmId }, language });
			const serialized = FlockSerializer.serialize(flock!);
			reply.success(serialized);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.put('/:id', { schema: updateFlockSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FlockParams; Body: FlockUpdate }>, reply) => {
		try {
			const { id } = request.params;
			const farmId = request.lastVisitedFarmId;
			const flockId = decodeId(id);

			if (!flockId) {
				return reply.error('Invalid flock ID', 400);
			}

			const flock = await fastify.flockService.updateFlock(flockId, farmId, request.body);

			if (!flock) {
				return reply.error('Flock not found', 404);
			}

			const serialized = FlockSerializer.serialize(flock);
			reply.success(serialized);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.delete('/:id', { schema: deleteFlockSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FlockParams }>, reply) => {
		try {
			const { id } = request.params;
			const farmId = request.lastVisitedFarmId;
			const flockId = decodeId(id);

			if (!flockId) {
				return reply.error('Invalid flock ID', 400);
			}

			const deleted = await fastify.flockService.deleteFlock(flockId, farmId);

			if (!deleted) {
				return reply.error('Flock not found', 404);
			}

			reply.success({ message: 'Flock deleted successfully' });
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default flockRoutes;
