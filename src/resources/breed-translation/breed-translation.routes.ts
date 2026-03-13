import { FastifyPluginAsync, FastifyRequest } from 'fastify';
import { createBreedTranslationSchema, CreateBreedTranslation } from './breed-translation.schema';
import { BreedTranslationSerializer } from './breed-translation.serializer';
import { decodeId } from '../../utils/id-hash-util';

const breedTranslationRoutes: FastifyPluginAsync = async (fastify) => {
	fastify.post('/', {
		schema: createBreedTranslationSchema,
	}, async (request: FastifyRequest<{ Body: CreateBreedTranslation }>, reply) => {
		try {
			const { breedId, language, name } = request.body;
			const decodedBreedId = decodeId(breedId);
			const breedTranslation = await fastify.breedTranslationService.createBreedTranslation({
				breedId: decodedBreedId!,
				language,
				name,
			});
			const serializedBreedTranslation = BreedTranslationSerializer.serialize(breedTranslation);
			reply.success(serializedBreedTranslation);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default breedTranslationRoutes;
