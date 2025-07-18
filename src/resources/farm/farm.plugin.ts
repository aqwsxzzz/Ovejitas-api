import { FastifyPluginAsync } from 'fastify';
import { createFarmSchema, farmSchemas } from './farm.schema';
import { FarmService } from './farm.service';
import { FarmSerializer } from './farm.serializer';

const farmPlugin: FastifyPluginAsync = async (fastify) => {
	farmSchemas.forEach(schema => fastify.addSchema(schema));

	const farmService = new FarmService(fastify.db);

	fastify.decorate('farmService', farmService);

	fastify.post('/farms', { schema: createFarmSchema, preHandler: fastify.authenticate }, async (request, reply) => {
		try {
			const farmData = request.body;
			const newFarm = await fastify.farmService.createFarm(farmData);
			const serializedFarm = FarmSerializer.serialize(newFarm);
			reply.success(serializedFarm, 'Farm created successfully');
		} catch (error) {
			console.error('Error creating farm:', error);
			fastify.handleDbError(error, reply);
		}
	});
};

export default farmPlugin;
