import { FastifyInstance } from "fastify";
import * as speciesController from "../../controllers/v1/species-controller";
import { speciesCreateSchema, speciesUpdateSchema } from "../../schemas/species-schema";
import { speciesResponseSchema } from "../../serializers/species-serializer";

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

	fastify.get(
		"/species",
		{
			preHandler: [fastify.authenticate],
			schema: {
				response: { 200: { type: "array", items: speciesResponseSchema } },
			},
		},
		speciesController.getSpecies
	);

	fastify.put(
		"/species/:id",
		{
			preHandler: [fastify.authenticate],
			schema: {
				body: speciesUpdateSchema,
				response: { 200: speciesResponseSchema },
			},
		},
		speciesController.updateSpecies
	);

	fastify.delete(
		"/species/:id",
		{
			preHandler: [fastify.authenticate],
		},
		speciesController.deleteSpecies
	);
}
