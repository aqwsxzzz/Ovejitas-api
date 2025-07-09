import "fastify";
import { Sequelize } from "sequelize";

declare module "fastify" {
	interface FastifyInstance {
		sequelize: Sequelize;
		authenticate(request: FastifyRequest, reply: FastifyReply): Promise<void>;
	}

	interface FastifyRequest {
		user: {
			id: number;
			email: string;
			role: string;
		} | null;
		lastVisitedFarmId: number;
		language: string;
	}
}
