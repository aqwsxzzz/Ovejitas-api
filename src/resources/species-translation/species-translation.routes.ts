import { FastifyPluginAsync, FastifyRequest } from 'fastify';
import { createSpeciesTranslationSchema, CreateSpeciesTranslation } from './species-translation.schema';
import { SpeciesTranslationSerializer } from './species-translation.serializer';

const speciesTranslationRoutes: FastifyPluginAsync = async (fastify) => {
	fastify.post('/', {
		schema: createSpeciesTranslationSchema,
	}, async (request: FastifyRequest<{ Body: CreateSpeciesTranslation }>, reply) => {
		try {
			const speciesTranslationData = request.body;
			const speciesTranslation = await fastify.speciesTranslationService.createSpeciesTranslation(speciesTranslationData);
			const serializedSpeciesTranslation = SpeciesTranslationSerializer.serialize(speciesTranslation);
			reply.success(serializedSpeciesTranslation);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default speciesTranslationRoutes;
