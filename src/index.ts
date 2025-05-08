import Fastify, { FastifyInstance } from "fastify";
import sequelizePlugin from "./plugins/sequelize-plugin";

const server: FastifyInstance = Fastify({
	logger: true,
});

server.register(sequelizePlugin);

server.get("/ping", async (request, reply) => {
	return { status: "ok", message: "pong 342" };
});

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
