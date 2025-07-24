import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { BreedCreate, breedSchemas, createBreedSchema } from './breed.schema';
import { BreedService } from './breed.service';
import { decodeId } from '../../utils/id-hash-util';
import { BreedSerializer } from './breed.serializer';

const breedPlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {
	breedSchemas.forEach((schema) => {
		fastify.addSchema(schema);
	});

	const breedService = new BreedService(fastify.db);

	fastify.post('/breeds', { schema: createBreedSchema }, async (request: FastifyRequest<{Body: BreedCreate}>, reply) => {
		const { name, speciesId } = request.body;
		const decodedId = decodeId(speciesId);
		const breed = await breedService.createBreed({ name, speciesId: decodedId! });
		const serializedBreed = BreedSerializer.serialize(breed);
		reply.success(serializedBreed);
	});
};

export default breedPlugin;
