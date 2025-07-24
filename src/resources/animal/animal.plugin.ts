import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import {  AnimalCreate, AnimalResponseSchema, animalSchemas, createAnimalSchema } from './animal.schema';
import { AnimalService } from './animal.service';
import { AnimalSerializer } from './animal.serializer';

const animalPlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	animalSchemas.forEach((schema) => {
		fastify.addSchema(schema);
	});

	const animalService = new AnimalService(fastify.db);

	fastify.get('/animals', { schema:AnimalResponseSchema , preHandler: fastify.authenticate }, async (request: FastifyRequest, reply) => {
		try {

			const farmId = request.lastVisitedFarmId;
			const animals = await animalService.getAnimals(farmId);
			const serializedAnimals = AnimalSerializer.serializeMany(animals!);
			reply.success(serializedAnimals);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.post('/animals', { schema:createAnimalSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Body: AnimalCreate}>, reply) => {
		try {

			const farmId = request.lastVisitedFarmId;
			const animal = await animalService.createAnimal({ data: { ...request.body, farmId } });
			const serializedAnimal = AnimalSerializer.serialize(animal!);
			reply.success(serializedAnimal);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default animalPlugin;
