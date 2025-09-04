import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { AnimalCreate, AnimalBulkCreate, AnimalInclude, AnimalParams, createAnimalSchema, listAnimalSchema, getAnimalByIdSchema, bulkCreateAnimalSchema, getAnimalDashboardSchema } from './animal.schema';
import { AnimalSerializer } from './animal.serializer';
import { decodeId } from '../../utils/id-hash-util';
import { UserLanguage } from '../user/user.schema';

const animalRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	fastify.get('/', { schema: listAnimalSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Querystring: AnimalInclude}>, reply) => {
		try {
			const { include, language } = request.query;
			const farmId = request.lastVisitedFarmId;
			const filters = fastify.animalService.extractFilterParams(request.query );

			const animals = await fastify.animalService.getAnimals(farmId, language, include, filters);

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

	fastify.post('/bulk', { schema: bulkCreateAnimalSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Body: AnimalBulkCreate}>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const result = await fastify.animalService.bulkCreateAnimals({ data: { ...request.body, farmId } });

			// Serialize the created animals
			const serializedResult = {
				created: AnimalSerializer.serializeMany(result.created),
				failed: result.failed,
			};

			reply.success(serializedResult);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/dashboard', { schema: getAnimalDashboardSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Querystring: { language: UserLanguage }}>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const { language } = request.query;

			const dashboardData = await fastify.animalService.getAnimalDashboard({ farmId, language });
			const serializedData = AnimalSerializer.serializeDashboard(dashboardData);

			reply.success(serializedData);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default animalRoutes;

