import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { BreedCreate, createBreedSchema } from './breed.schema';
import { decodeId } from '../../utils/id-hash-util';
import { BreedSerializer } from './breed.serializer';

const breedRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {
	// Routes now use the decorated service instead of creating a new instance

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
