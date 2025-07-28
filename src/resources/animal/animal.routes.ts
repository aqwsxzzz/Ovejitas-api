import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { AnimalCreate, AnimalInclude, AnimalParams, createAnimalSchema, listAnimalSchema, getAnimalByIdSchema } from './animal.schema';
import { AnimalSerializer } from './animal.serializer';
import { decodeId } from '../../utils/id-hash-util';

const animalRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {
	// Routes now use the decorated service instead of creating a new instance

	fastify.get('/', { schema: listAnimalSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Querystring: AnimalInclude}>, reply) => {
		try {
			const { include, language } = request.query;
			const farmId = request.lastVisitedFarmId;
			const animals = await fastify.animalService.getAnimals(farmId, language,  include);

			const serializedAnimals = AnimalSerializer.serializeMany(animals!);

			reply.success(serializedAnimals);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/:id', { schema: getAnimalByIdSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Params: AnimalParams, Querystring: AnimalInclude}>, reply) => {
		try {
			const { id } = request.params;
			const { include, language } = request.query;
			const animalId = decodeId(id);

			if (!animalId) {
				return reply.error('Invalid animal ID', 400);
			}

			const animal = await fastify.animalService.getAnimalById(animalId, language,  include);

			if (!animal) {
				return reply.error('Animal not found', 404);
			}

			const serializedAnimal = AnimalSerializer.serialize(animal);
			reply.success(serializedAnimal);
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

