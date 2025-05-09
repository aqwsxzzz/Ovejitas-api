import { FastifyInstance } from "fastify";
import * as userController from "../../controllers/v1/user-controller";
import { userUpdateSchema } from "../../schemas/user-schema";
import { userResponseSchema } from "../../serializers/user-serializer";

export default async function userRoutes(fastify: FastifyInstance) {
	fastify.put("/users/:id", { preHandler: [fastify.authenticate], schema: { body: userUpdateSchema, response: { 200: userResponseSchema } } }, userController.updateUser);
	fastify.delete("/users/:id", { preHandler: [fastify.authenticate] }, userController.deleteUser);
}
