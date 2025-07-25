import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { createSpeciesSchema,  getSpeciesSchema,  listSpeciesSchema, SpeciesCreateInput, SpeciesQueryString, SpeciesParams } from './species.schema';
import { SpeciesService } from './species.service';
import { SpeciesSerializer } from './species.serializer';
import { decodeId } from '../../utils/id-hash-util';

const speciesPlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {

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

	fastify.get('/species', { schema: listSpeciesSchema,  preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Querystring:  SpeciesQueryString }>, reply) => {
		try {
			const { include, order } = request.query;
			const species = await speciesService.getAllSpecies(include, order);
			const serializedSpecies = SpeciesSerializer.serializeMany(species);
			reply.success(serializedSpecies);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/species/:id', { schema: getSpeciesSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{ Params: SpeciesParams, Querystring: SpeciesQueryString }>, reply) => {
		try {
			const { id } = request.params;
			const species = await speciesService.getSpeciesById(decodeId(id)!, request.query.include);
			const serializedSpecies = SpeciesSerializer.serialize(species!);
			reply.success(serializedSpecies);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default speciesPlugin;
