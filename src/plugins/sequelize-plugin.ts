import fp from "fastify-plugin";
import { Sequelize } from "sequelize";
import { FastifyInstance } from "fastify";
import sequelizeConfig from "../config/sequelize-config";

// Type augmentation for FastifyInstance
declare module "fastify" {
	interface FastifyInstance {
		sequelize: Sequelize;
	}
}

const sequelize = new Sequelize(sequelizeConfig);

export default fp(async (fastify: FastifyInstance) => {
	try {
		await sequelize.authenticate();
		fastify.decorate("sequelize", sequelize);
		fastify.log.info("Sequelize connection established");
	} catch (error) {
		fastify.log.error("Unable to connect to the database:", error);
		throw error;
	}
});
