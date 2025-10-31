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

	},

	production: {
		dialect: 'postgres',
		username: process.env.DB_USER,
		password: process.env.DB_PASS,
		database: process.env.DB_NAME,
		host: process.env.DB_HOST,
		port: Number(process.env.DB_PORT),
		dialect: process.env.DB_DIALECT,
		logging: false,
		dialectOptions: {
			ssl: {
				require: true,
				rejectUnauthorized: false,
			},
		},
	},
};
