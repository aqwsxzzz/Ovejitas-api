import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	EggCollectionParams,
	EggCollectionItemParams,
	EggCollectionCreate,
	EggCollectionUpdate,
	EggCollectionQuery,
	listEggCollectionsSchema,
	createEggCollectionSchema,
	updateEggCollectionSchema,
	deleteEggCollectionSchema,
} from './egg-collection.schema';
import { decodeId } from '../../utils/id-hash-util';
import { EggCollectionSerializer } from './egg-collection.serializer';
import { parsePagination } from '../../utils/pagination';

const eggCollectionRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	fastify.get('/flocks/:flockId/egg-collections', { schema: listEggCollectionsSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: EggCollectionParams, Querystring: EggCollectionQuery }>, reply) => {
		try {
			const { flockId } = request.params;
			const decodedFlockId = decodeId(flockId)!;
			const pagination = parsePagination(request.query);

			const flock = await fastify.flockService.getFlockById(decodedFlockId, 'EN' as never);
			if (!flock) {
				return reply.error('Flock not found', 404);
			}

			const result = await fastify.eggCollectionService.getEggCollections(decodedFlockId, pagination);
			const serialized = EggCollectionSerializer.serializeMany(result.rows, flock.currentCount);
			reply.successWithPagination(serialized, result.pagination);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.post('/flocks/:flockId/egg-collections', { schema: createEggCollectionSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: EggCollectionParams, Body: EggCollectionCreate }>, reply) => {
		try {
			const { flockId } = request.params;
			const userId = request.user!.id;
			const decodedFlockId = decodeId(flockId)!;

			const collection = await fastify.eggCollectionService.createEggCollection({
				flockId: decodedFlockId,
				data: request.body,
				userId,
			});

			const flock = await fastify.flockService.getFlockById(decodedFlockId, 'EN' as never);
			const serialized = EggCollectionSerializer.serialize(collection, flock!.currentCount);
			reply.success(serialized);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.put('/flocks/:flockId/egg-collections/:id', { schema: updateEggCollectionSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: EggCollectionItemParams, Body: EggCollectionUpdate }>, reply) => {
		try {
			const { flockId, id } = request.params;
			const decodedFlockId = decodeId(flockId)!;
			const collectionId = decodeId(id)!;

			const collection = await fastify.eggCollectionService.updateEggCollection({
				flockId: decodedFlockId,
				collectionId,
				data: request.body,
			});

			const flock = await fastify.flockService.getFlockById(decodedFlockId, 'EN' as never);
			const serialized = EggCollectionSerializer.serialize(collection, flock!.currentCount);
			reply.success(serialized);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.delete('/flocks/:flockId/egg-collections/:id', { schema: deleteEggCollectionSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: EggCollectionItemParams }>, reply) => {
		try {
			const { flockId, id } = request.params;
			await fastify.eggCollectionService.deleteEggCollection({
				flockId: decodeId(flockId)!,
				collectionId: decodeId(id)!,
			});
			reply.success(null);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default eggCollectionRoutes;
