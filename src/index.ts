import Fastify, { FastifyInstance } from "fastify";
import sequelizePlugin from "./plugins/sequelize-plugin";
import responseWrapperPlugin from "./plugins/response-wrapper-plugin";
import userRoutes from "./routes/v1/user-route";
import authRoutes from "./routes/v1/auth-route";

const server: FastifyInstance = Fastify({
	logger: true,
});

server.register(sequelizePlugin);
server.register(responseWrapperPlugin);
server.register(userRoutes, { prefix: "/v1" });
server.register(authRoutes, { prefix: "/v1" });

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
