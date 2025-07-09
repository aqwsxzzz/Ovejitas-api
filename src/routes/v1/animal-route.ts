import { FastifyInstance } from "fastify";
import * as animalController from "../../controllers/v1/animal-controller";
import { animalCreateSchema, animalUpdateSchema, animalIdParamSchema, animalListParamSchema } from "../../schemas/animal-schema";
import { animalResponseSchema } from "../../serializers/animal-serializer";
import { AnimalCreateRoute, AnimalUpdateRoute, AnimalGetRoute, AnimalDeleteRoute } from "../../types/animal-types";

export default async function animalRoute(fastify: FastifyInstance) {
	fastify.get<AnimalGetRoute>(
		"/farms/:farmId/animals/:id",
		{
			preHandler: [fastify.authenticate],
			schema: {
				params: animalIdParamSchema,
				response: {
					200: animalResponseSchema,
					404: { type: "object", properties: { message: { type: "string" } }, required: ["message"] },
				},
			},
		},
		animalController.getAnimalById
	);

	fastify.get(
		"/farms/:farmId/animals",
		{
			preHandler: [fastify.authenticate],
			schema: {
				params: animalListParamSchema,
				response: {
					200: { type: "array", items: animalResponseSchema },
				},
			},
		},
		animalController.listAnimalsByFarm
	);

	fastify.post<AnimalCreateRoute>(
		"/farms/:farmId/animals",
		{
			preHandler: [fastify.authenticate],
			schema: {
				body: animalCreateSchema,
				response: {
					201: animalResponseSchema,
					409: { type: "object", properties: { message: { type: "string" } }, required: ["message"] },
				},
			},
		},
		animalController.createAnimal
	);

	fastify.put<AnimalUpdateRoute>(
		"/farms/:farmId/animals/:id",
		{
			preHandler: [fastify.authenticate],
			schema: {
				params: animalIdParamSchema,
				body: animalUpdateSchema,
				response: {
					200: animalResponseSchema,
					404: { type: "object", properties: { message: { type: "string" } }, required: ["message"] },
					409: { type: "object", properties: { message: { type: "string" } }, required: ["message"] },
				},
			},
		},
		animalController.updateAnimal
	);

	fastify.delete<AnimalDeleteRoute>(
		"/farms/:farmId/animals/:id",
		{
			preHandler: [fastify.authenticate],
			schema: {
				params: animalIdParamSchema,
				response: {
					200: { type: "object", properties: { message: { type: "string" } }, required: ["message"] },
					404: { type: "object", properties: { message: { type: "string" } }, required: ["message"] },
				},
			},
		},
		animalController.deleteAnimal
	);
}
