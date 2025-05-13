import { FastifyInstance } from "fastify";
import * as farmController from "../../controllers/v1/farm-controller";
import { farmCreateSchema, farmUpdateSchema } from "../../schemas/farm-schema";
import { farmResponseSchema } from "../../serializers/farm-serializer";
import { IFarmIdParam, FarmUpdateRoute } from "../../types/farm-types";

export default async function farmRoutes(fastify: FastifyInstance) {
	fastify.post(
		"/farms",
		{
			preHandler: [fastify.authenticate],
			schema: {
				body: farmCreateSchema,
				response: { 201: farmResponseSchema },
			},
		},
		farmController.createFarm
	);

	fastify.get(
		"/farms",
		{
			preHandler: [fastify.authenticate],
			schema: {
				response: { 200: { type: "array", items: farmResponseSchema } },
			},
		},
		farmController.getFarms
	);

	fastify.get<{ Params: IFarmIdParam }>(
		"/farms/:id",
		{
			preHandler: [fastify.authenticate],
			schema: {
				response: { 200: farmResponseSchema },
			},
		},
		farmController.getFarmById
	);

	fastify.put<FarmUpdateRoute>(
		"/farms/:id",
		{
			preHandler: [fastify.authenticate],
			schema: {
				body: farmUpdateSchema,
				response: { 200: farmResponseSchema },
			},
		},
		farmController.updateFarm
	);

	fastify.delete<{ Params: IFarmIdParam }>(
		"/farms/:id",
		{
			preHandler: [fastify.authenticate],
		},
		farmController.deleteFarm
	);
}
