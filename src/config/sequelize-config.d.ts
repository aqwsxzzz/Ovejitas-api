import { Options } from "sequelize";

export interface SequelizeConfig {
	[key: string]: Options;
	development: Options;
	test: Options;
	production: Options;
}

declare const config: SequelizeConfig;
export = config;
