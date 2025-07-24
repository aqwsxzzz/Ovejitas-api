import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { createSpeciesSchema,  listSpeciesSchema, SpeciesCreateInput, SpeciesInclude, speciesSchemas } from './species.schema';
import { SpeciesService } from './species.service';
import { SpeciesSerializer } from './species.serializer';

const speciesPlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {
	speciesSchemas.forEach(schema => fastify.addSchema(schema));

	const speciesService = new SpeciesService(fastify.db);

	fastify.post('/species', { schema: createSpeciesSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Body: SpeciesCreateInput }>, reply) => {
		try {
			const speciesData = request.body;
			const { species } = await speciesService.createSpecies(speciesData);
			const serializedSpecies = SpeciesSerializer.serialize(species);
			reply.success(serializedSpecies);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/species', { schema: listSpeciesSchema,  preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Querystring: SpeciesInclude }>, reply) => {
		try {
			const { include } = request.query;
			const species = await speciesService.getAllSpecies(include);
			const serializedSpecies = SpeciesSerializer.serializeMany(species);
			reply.success(serializedSpecies);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default speciesPlugin;
