/// <reference path="../types/fastify.d.ts" />

import Fastify, { FastifyInstance } from "fastify";
import sequelizePlugin from "./plugins/sequelize-plugin";
import responseWrapperPlugin from "./plugins/response-wrapper-plugin";
import userRoutes from "./routes/v1/user-route";
import authRoutes from "./routes/v1/auth-route";
import fastifyCookie from "@fastify/cookie";
import authPlugin from "./plugins/auth-plugin";
import fastifyCors from "@fastify/cors";
import speciesRoutes from "./routes/v1/species-route";
import speciesTranslationRoutes from "./routes/v1/species-translation-routes";
import "./models/associations";
import farmRoutes from "./routes/v1/farm-route";
import farmMembersRoutes from "./routes/v1/farm-members-route";
import farmInvitationRoutes from "./routes/v1/farm-invitation-route";

const server: FastifyInstance = Fastify({
	logger: true,
});

server.register(fastifyCors, {
	origin: ["http://localhost:5173"],
	credentials: true,
});

server.register(sequelizePlugin);
server.register(authPlugin);
server.register(responseWrapperPlugin);
server.register(fastifyCookie);
server.register(userRoutes, { prefix: "/v1" });
server.register(speciesRoutes, { prefix: "/v1" });
server.register(speciesTranslationRoutes, { prefix: "/v1" });
server.register(authRoutes, { prefix: "/v1" });
server.register(farmRoutes, { prefix: "/v1" });
server.register(farmMembersRoutes, { prefix: "/v1" });
server.register(farmInvitationRoutes, { prefix: "/v1" });

const start = async () => {
	try {
		await server.listen({ port: 8080, host: "0.0.0.0" });
		console.log(`Server is running at ${server.server.address()}`);
	} catch (err) {
		server.log.error(err);
		process.exit(1);
	}
};

start();
