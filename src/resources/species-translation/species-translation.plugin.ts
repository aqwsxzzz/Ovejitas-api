import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { createSpeciesTranslationSchema, CreateSpeciesTranslation } from './species-translation.schema';
import { SpeciesTranslationService } from './species-translation.service';
import { SpeciesTranslationSerializer } from './species-translation.serializer';

const speciesTranslationPlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	const speciesTranslationService = new SpeciesTranslationService(fastify.db);

	fastify.post('/species-translations', { schema: createSpeciesTranslationSchema }, async (request: FastifyRequest< { Body: CreateSpeciesTranslation }>, reply) => {
		try {
			const speciesTranslationData = request.body;
			const speciesTranslation = await speciesTranslationService.createSpeciesTranslation(speciesTranslationData);
			const serializedSpeciesTranslation = SpeciesTranslationSerializer.serialize(speciesTranslation);
			reply.success(serializedSpeciesTranslation);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default speciesTranslationPlugin;
