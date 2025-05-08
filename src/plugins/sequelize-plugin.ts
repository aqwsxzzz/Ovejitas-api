import fp from "fastify-plugin";
import { Options, Sequelize } from "sequelize";
import { FastifyInstance } from "fastify";
import sequelizeConfig = require("../config/sequelize-config");

const env = (process.env.NODE_ENV || "development") as keyof typeof sequelizeConfig;
const envConfig = sequelizeConfig[env] as Options;

declare module "fastify" {
	interface FastifyInstance {
		sequelize: Sequelize;
	}
}

const sequelize = new Sequelize(envConfig);

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
