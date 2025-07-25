import { FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	createSpeciesSchema,
	getSpeciesSchema,
	listSpeciesSchema,
	SpeciesCreateInput,
	SpeciesQueryString,
	SpeciesParams,
} from './species.schema';
import { SpeciesSerializer } from './species.serializer';
import { decodeId } from '../../utils/id-hash-util';

const speciesRoutes: FastifyPluginAsync = async (fastify) => {
	fastify.post('/', {
		schema: createSpeciesSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Body: SpeciesCreateInput }>, reply) => {
		try {
			const speciesData = request.body;
			const { species } = await fastify.speciesService.createSpecies(speciesData);
			const serializedSpecies = SpeciesSerializer.serialize(species);
			reply.success(serializedSpecies);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/', {
		schema: listSpeciesSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Querystring: SpeciesQueryString }>, reply) => {
		try {
			const { include, order } = request.query;
			const species = await fastify.speciesService.getAllSpecies(include, order);
			const serializedSpecies = SpeciesSerializer.serializeMany(species);
			reply.success(serializedSpecies);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/:id', {
		schema: getSpeciesSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: SpeciesParams, Querystring: SpeciesQueryString }>, reply) => {
		try {
			const { id } = request.params;
			const species = await fastify.speciesService.getSpeciesById(decodeId(id)!, request.query.include);
			const serializedSpecies = SpeciesSerializer.serialize(species!);
			reply.success(serializedSpecies);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default speciesRoutes;
