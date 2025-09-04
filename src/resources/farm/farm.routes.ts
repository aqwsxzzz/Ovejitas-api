import { FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	createFarmSchema,
	deleteFarmSchema,
	FarmCreateInput,
	FarmParams,
	FarmUpdateInput,
	getFarmSchema,
	updateFarmSchema,
} from './farm.schema';
import { FarmSerializer } from './farm.serializer';
import { decodeId } from '../../utils/id-hash-util';

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
		preHandler: fastify.authenticate,
	}, async (request, reply) => {
		try {
			const farms = await fastify.farmService.getFarms(request.user!.id);
			const serializedFarms = farms.map(FarmSerializer.serialize);
			reply.success(serializedFarms, 'Farms retrieved successfully');
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
