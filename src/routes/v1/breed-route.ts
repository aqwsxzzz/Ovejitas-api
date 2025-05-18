import { FastifyInstance } from "fastify";
import * as breedController from "../../controllers/v1/breed-controller";
import { breedCreateSchema, breedUpdateSchema, breedIdParamSchema } from "../../schemas/breed-schema";
import { breedResponseSchema } from "../../serializers/breed-serializer";

export default async function breedRoutes(fastify: FastifyInstance) {
	fastify.post(
		"/breeds",
		{
			preHandler: [fastify.authenticate],
			schema: {
				body: breedCreateSchema,
				response: { 201: breedResponseSchema },
			},
		},
		breedController.createBreed
	);

	fastify.get(
		"/breeds",
		{
			preHandler: [fastify.authenticate],
			schema: {
				response: { 200: { type: "array", items: breedResponseSchema } },
			},
		},
		breedController.listBreeds
	);

	fastify.get(
		"/breeds/:id",
		{
			preHandler: [fastify.authenticate],
			schema: {
				params: breedIdParamSchema,
				response: { 200: breedResponseSchema },
			},
		},
		breedController.getBreedById
	);

	fastify.put(
		"/breeds/:id",
		{
			preHandler: [fastify.authenticate],
			schema: {
				params: breedIdParamSchema,
				body: breedUpdateSchema,
				response: { 200: breedResponseSchema },
			},
		},
		breedController.updateBreed
	);

	fastify.delete(
		"/breeds/:id",
		{
			preHandler: [fastify.authenticate],
			schema: {
				params: breedIdParamSchema,
			},
		},
		breedController.deleteBreed
	);
}
