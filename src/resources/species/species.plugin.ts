import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { createSpeciesSchema, SpeciesCreateInput, speciesSchemas } from './species.schema';
import { SpeciesService } from './species.service';
import { SpeciesSerializer } from './species.serializer';

const speciesPlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {
	speciesSchemas.forEach(schema => fastify.addSchema(schema));

	const speciesService = new SpeciesService(fastify.db);

	fastify.post('/species', { schema: createSpeciesSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Body: SpeciesCreateInput }>, reply) => {
		try {
			const speciesData = request.body;
			const { species, translation } = await speciesService.createSpecies(speciesData);
			const serializedSpecies = SpeciesSerializer.serialize(species, translation);
			reply.success(serializedSpecies);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default speciesPlugin;
