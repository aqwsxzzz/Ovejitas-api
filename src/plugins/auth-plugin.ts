import fp from "fastify-plugin";
import { FastifyInstance, FastifyRequest, FastifyReply } from "fastify";
import jwt from "jsonwebtoken";

const JWT_SECRET = process.env.JWT_SECRET || "your_jwt_secret";

export default fp(async function authPlugin(fastify: FastifyInstance) {
	fastify.decorate("authenticate", async function (request: FastifyRequest, reply: FastifyReply) {
		try {
			const token = request.cookies.jwt;
			if (!token) throw new Error("No token");

			const decoded = jwt.verify(token, JWT_SECRET) as { id: number; email: string; role: string };
			request.user = decoded;
		} catch (err) {
			request.user = null;
			reply.code(401).send({ message: "Unauthorized" });
			return;
		}
	});
});
