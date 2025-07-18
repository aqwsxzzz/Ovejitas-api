import { FastifyPluginAsync } from 'fastify';
import { createFarmSchema, FarmCreateInput, farmSchemas } from './farm.schema';
import { FarmService } from './farm.service';
import { FarmSerializer } from './farm.serializer';

const farmPlugin: FastifyPluginAsync = async (fastify) => {
	farmSchemas.forEach(schema => fastify.addSchema(schema));

	const farmService = new FarmService(fastify.db);

	fastify.post('/farms', { schema: createFarmSchema, preHandler: fastify.authenticate }, async (request, reply) => {
		try {
			const farmData = request.body as FarmCreateInput;
			const newFarm = await farmService.createFarm(farmData);
			const serializedFarm = FarmSerializer.serialize(newFarm);
			reply.success(serializedFarm, 'Farm created successfully');
		} catch (error) {
			console.error('Error creating farm:', error);
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/farms', { preHandler: fastify.authenticate }, async (request, reply) => {
		try {
			const farms = await farmService.getFarms(request.user!.id);
			const serializedFarms = farms.map(FarmSerializer.serialize);
			reply.success(serializedFarms, 'Farms retrieved successfully');
		} catch (error) {
			console.error('Error retrieving farms:', error);
			fastify.handleDbError(error, reply);
		}
	});
};

export default farmPlugin;
