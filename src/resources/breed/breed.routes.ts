import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { BreedCreate, BreedQuery, createBreedSchema, getBreedsSchema } from './breed.schema';
import { decodeId } from '../../utils/id-hash-util';
import { BreedSerializer } from './breed.serializer';
import { UserLanguage } from '../user/user.schema';
import { parsePagination } from '../../utils/pagination';

const breedRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	fastify.get('/', { schema: getBreedsSchema }, async (request: FastifyRequest<{Querystring: BreedQuery}>, reply) => {
		try {
			const { speciesId, order, include, language } = request.query;
			const decodedSpeciesId = decodeId(speciesId);
			const pagination = parsePagination(request.query);
			const result = await fastify.breedService.getBreedsBySpecies(
				decodedSpeciesId!,
				order,
				include,
				language as UserLanguage | undefined,
				pagination ?? undefined,
			);

			if (pagination && !Array.isArray(result)) {
				const serializedBreeds = result.rows.map(breed => BreedSerializer.serialize(breed));
				return reply.successWithPagination(serializedBreeds, result.pagination);
			}

			const breeds = Array.isArray(result) ? result : result.rows;
			const serializedBreeds = breeds.map(breed => BreedSerializer.serialize(breed));
			reply.success(serializedBreeds);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.post('/', { schema: createBreedSchema }, async (request: FastifyRequest<{Body: BreedCreate}>, reply) => {
		try {
			const { name, speciesId, language } = request.body;
			const decodedId = decodeId(speciesId);
			const { breed, translation } = await fastify.breedService.createBreed({
				name,
				language,
				speciesId: decodedId!,
			});
			const serializedBreed = BreedSerializer.serialize(breed, [translation]);
			reply.success(serializedBreed);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default breedRoutes;
