import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { BreedCreate, BreedQuery, createBreedSchema, getBreedsSchema } from './breed.schema';
import { decodeId } from '../../utils/id-hash-util';
import { BreedSerializer } from './breed.serializer';

const breedRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	fastify.get('/', { schema: getBreedsSchema }, async (request: FastifyRequest<{Querystring: BreedQuery}>, reply) => {
		try {
			const { speciesId, order } = request.query;
			const decodedSpeciesId = decodeId(speciesId);
			const breeds = await fastify.breedService.getBreedsBySpecies(decodedSpeciesId!, order);
			const serializedBreeds = breeds.map(breed => BreedSerializer.serialize(breed));
			reply.success(serializedBreeds);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.post('/', { schema: createBreedSchema }, async (request: FastifyRequest<{Body: BreedCreate}>, reply) => {
		try {
			const { name, speciesId } = request.body;
			const decodedId = decodeId(speciesId);
			const breed = await fastify.breedService.createBreed({ name, speciesId: decodedId! });
			const serializedBreed = BreedSerializer.serialize(breed);
			reply.success(serializedBreed);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default breedRoutes;
