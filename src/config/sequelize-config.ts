import { Dialect } from "sequelize";

interface SequelizeConfig {
	username: string;
	password: string;
	database: string;
	host: string;
	port: number;
	dialect: Dialect;
	logging: boolean;
}

const config: SequelizeConfig = {
	username: process.env.DB_USER || "user",
	password: process.env.DB_PASS || "password",
	database: process.env.DB_NAME || "database",
	host: process.env.DB_HOST || "localhost",
	port: Number(process.env.DB_PORT) || 5432,
	dialect: (process.env.DB_DIALECT as Dialect) || "postgres",
	logging: process.env.NODE_ENV !== "production",
};

export default config;
