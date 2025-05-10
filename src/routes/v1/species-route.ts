import { FastifyInstance } from "fastify";
import * as speciesController from "../../controllers/v1/species-controller";
import { speciesCreateSchema } from "../../schemas/species-schema";
import { speciesResponseSchema } from "../../serializers/species-serializer";
import { IGetSpeciesByIdQuery, ISpeciesIdParam, SpeciesListParams } from "../../types/species-types";

export default async function speciesRoutes(fastify: FastifyInstance) {
	fastify.post(
		"/species",
		{
			preHandler: [fastify.authenticate],
			schema: {
				body: speciesCreateSchema,
				response: { 201: speciesResponseSchema },
			},
		},
		speciesController.createSpecies
	);

	fastify.get<{ Querystring: SpeciesListParams }>(
		"/species",
		{
			preHandler: [fastify.authenticate],
			schema: {
				response: { 200: { type: "array", items: speciesResponseSchema } },
			},
		},
		speciesController.getSpecies
	);

	fastify.get<{ Params: ISpeciesIdParam; Querystring: IGetSpeciesByIdQuery }>(
		"/species/:id",
		{
			preHandler: [fastify.authenticate],
		},
		speciesController.getSpeciesById
	);
	fastify.delete<{ Params: ISpeciesIdParam }>(
		"/species/:id",
		{
			preHandler: [fastify.authenticate],
		},
		speciesController.deleteSpecies
	);
}
