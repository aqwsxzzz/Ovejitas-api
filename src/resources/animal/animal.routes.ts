import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { AnimalCreate, AnimalInclude, createAnimalSchema, listAnimalSchema } from './animal.schema';
import { AnimalSerializer } from './animal.serializer';

const animalRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {
	// Routes now use the decorated service instead of creating a new instance

	fastify.get('/', { schema: listAnimalSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Querystring: AnimalInclude}>, reply) => {
		try {
			const { include } = request.query;
			const farmId = request.lastVisitedFarmId;
			const animals = await fastify.animalService.getAnimals(farmId, include);

			const serializedAnimals = AnimalSerializer.serializeMany(animals!);

			reply.success(serializedAnimals);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.post('/', { schema: createAnimalSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Body: AnimalCreate}>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const animal = await fastify.animalService.createAnimal({ data: { ...request.body, farmId } });
			const serializedAnimal = AnimalSerializer.serialize(animal!);
			reply.success(serializedAnimal);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default animalRoutes;

