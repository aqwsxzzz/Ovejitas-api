// eslint-disable-next-line @typescript-eslint/no-require-imports
require('dotenv').config();

module.exports = {
	development: {
		username: process.env.DB_USER || 'user',
		password: process.env.DB_PASS || 'password',
		database: process.env.DB_NAME || 'database',
		host: process.env.DB_HOST || 'localhost',
		port: Number(process.env.DB_PORT) || 5432,
		dialect: 'postgres',
		logging: process.env.NODE_ENV !== 'production',
		seederStorage: 'sequelize',
	},

	test: {
		username: process.env.DB_USER || 'username',
		password: process.env.DB_PASS || 'password',
		database: process.env.DB_NAME || 'ovejitas_test',
		host: process.env.DB_HOST || 'localhost',
		port: Number(process.env.DB_PORT) || 5432,
		dialect: 'postgres',
		logging: false,
		seederStorage: 'sequelize',
	},

	production: {
		dialect: 'postgres',
		username: process.env.DB_USER,
		password: process.env.DB_PASS,
		database: process.env.DB_NAME,
		host: process.env.DB_HOST,
		port: Number(process.env.DB_PORT),
		logging: false,
		seederStorage: 'sequelize',
		dialectOptions: {
			ssl: {
				require: true,
				rejectUnauthorized: false,
			},
		},
	},
};
