import { FastifyInstance } from "fastify";
import * as userController from "../../controllers/v1/user-controller";
import { userCreateSchema, userUpdateSchema } from "../../schemas/user-schema";
import { userResponseSchema } from "../../serializers/user-serializer";

export default async function userRoutes(fastify: FastifyInstance) {
	fastify.post("/users", { schema: { body: userCreateSchema, response: { 201: userResponseSchema } } }, userController.createUser);
	fastify.get("/users", { schema: { response: { 200: { type: "array", items: userResponseSchema } } } }, userController.listUsers);
	fastify.get("/users/:id", { schema: { response: { 200: userResponseSchema } } }, userController.getUser);
	fastify.put("/users/:id", { schema: { body: userUpdateSchema, response: { 200: userResponseSchema } } }, userController.updateUser);
	fastify.delete("/users/:id", userController.deleteUser);
}
