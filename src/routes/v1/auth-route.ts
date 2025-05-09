import { FastifyInstance } from "fastify";
import * as authController from "../../controllers/v1/auth-controller";

export default async function authRoutes(fastify: FastifyInstance) {
	fastify.post("/auth/signup", authController.signUp);
	fastify.post("/auth/login", authController.login);
	fastify.get("/auth/me", authController.getCurrentUser);
	fastify.post("/auth/logout", authController.logout);
}
