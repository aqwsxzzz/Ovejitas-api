import { FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	createFarmSchema,
	deleteFarmSchema,
	FarmCreateInput,
	FarmListQuery,
	FarmParams,
	FarmUpdateInput,
	getFarmSchema,
	listFarmsSchema,
	updateFarmSchema,
} from './farm.schema';
import { FarmSerializer } from './farm.serializer';
import { decodeId } from '../../utils/id-hash-util';
import { parsePagination } from '../../utils/pagination';

const farmRoutes: FastifyPluginAsync = async (fastify) => {
	// Create Farm
	fastify.post('/', {
		schema: createFarmSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Body: FarmCreateInput }>, reply) => {
		try {
			const farmData = request.body;
			const newFarm = await fastify.farmService.createFarm(farmData, request.user!.id);
			const serializedFarm = FarmSerializer.serialize(newFarm);
			reply.success(serializedFarm, 'Farm created successfully');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// Get Farms
	fastify.get('/', {
		schema: listFarmsSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Querystring: FarmListQuery }>, reply) => {
		try {
			const pagination = parsePagination(request.query);
			const result = await fastify.farmService.getFarms(request.user!.id, pagination);
			const serializedFarms = FarmSerializer.serializeMany(result.rows);
			reply.successWithPagination(serializedFarms, result.pagination);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// Get Farm
	fastify.get('/:farmId', {
		schema: getFarmSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: FarmParams }>, reply) => {
		try {
			const { farmId } = request.params;
			const decodedFarmId = decodeId(farmId)!;
			const  lastVisitedFarmId = request.lastVisitedFarmId;
			const farm = await fastify.farmService.getFarm(decodedFarmId);

			// Update user's lastVisitedFarmId if different from current
			if (request.user && lastVisitedFarmId !== decodedFarmId) {
				await fastify.userService.updateLastVisitedFarm(request.user.id, decodedFarmId);
			}

			const serializedFarm = FarmSerializer.serialize(farm);
			reply.success(serializedFarm, 'Farm retrieved successfully');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// Update Farm
	fastify.post('/:farmId', {
		schema: updateFarmSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: FarmParams, Body: FarmUpdateInput }>, reply) => {
		try {
			const { farmId } = request.params;
			const farmData = request.body;
			const decodedFarmId = decodeId(farmId)!;
			const farm = await fastify.farmService.updateFarm(decodedFarmId, farmData);
			const serializedFarm = FarmSerializer.serialize(farm);
			reply.success(serializedFarm, 'Farm updated successfully');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// Delete Farm
	fastify.delete('/:farmId', {
		schema: deleteFarmSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: FarmParams }>, reply) => {
		try {
			const { farmId } = request.params;
			const decodedFarmId = decodeId(farmId)!;
			await fastify.farmService.deleteFarm(decodedFarmId);
			reply.success('Farm deleted successfully');
		} catch (error) {
			console.error('Error deleting farm:', error);
			fastify.handleDbError(error, reply);
		}
	});
};

export default farmRoutes;
