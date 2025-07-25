import { FastifyPluginAsync, FastifyRequest } from 'fastify';
import { createFarmSchema, deleteFarmSchema, FarmCreateInput, FarmParams,  FarmUpdateInput, getFarmSchema, updateFarmSchema } from './farm.schema';
import { FarmService } from './farm.service';
import { FarmSerializer } from './farm.serializer';

const farmPlugin: FastifyPluginAsync = async (fastify) => {

	const farmService = new FarmService(fastify.db);

	// Create Farm
	fastify.post('/farms', { schema: createFarmSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Body: FarmCreateInput }>, reply) => {
		try {
			const farmData = request.body;
			const newFarm = await farmService.createFarm(farmData);
			const serializedFarm = FarmSerializer.serialize(newFarm);
			reply.success(serializedFarm, 'Farm created successfully');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// Get Farms
	fastify.get('/farms', { preHandler: fastify.authenticate }, async (request, reply) => {
		try {
			const farms = await farmService.getFarms(request.user!.id);
			const serializedFarms = farms.map(FarmSerializer.serialize);
			reply.success(serializedFarms, 'Farms retrieved successfully');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// Get Farm
	fastify.get('/farms/:farmId', { schema: getFarmSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FarmParams }>, reply) => {
		try {
			const { farmId } = request.params;
			const farm = await farmService.getFarm(farmId);
			const serializedFarm = FarmSerializer.serialize(farm);
			reply.success(serializedFarm, 'Farm retrieved successfully');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// Update Farm
	fastify.post('/farms/:farmId', { schema: updateFarmSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FarmParams, Body: FarmUpdateInput }>, reply) => {
		try {
			const { farmId } = request.params;
			const farmData = request.body;
			const farm = await farmService.updateFarm(farmId, farmData);
			const serializedFarm = FarmSerializer.serialize(farm);
			reply.success(serializedFarm, 'Farm updated successfully');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// Delete Farm
	fastify.delete('/farms/:farmId', { schema: deleteFarmSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: FarmParams }>, reply) => {
		try {
			const { farmId } = request.params;
			await farmService.deleteFarm(farmId);
			reply.success('Farm deleted successfully');
		} catch (error) {
			console.error('Error deleting farm:', error);
			fastify.handleDbError(error, reply);
		}
	});
};

export default farmPlugin;
