// eslint-disable-next-line @typescript-eslint/no-require-imports
require('dotenv').config();

module.exports = {
	development: {
		username: process.env.DB_USER || 'user',
		password: process.env.DB_PASS || 'password',
		database: process.env.DB_NAME || 'database',
		host: process.env.DB_HOST || 'localhost',
		port: Number(process.env.DB_PORT) || 5432,
		dialect: process.env.DB_DIALECT || 'postgres',
		logging: process.env.NODE_ENV !== 'production',
		dialectOptions: {
			ssl: process.env.DB_HOST && process.env.DB_HOST.includes('supabase') ? {
				require: true,
				rejectUnauthorized: false,
			} : false,
		},
	},
	test: {
		username: process.env.DB_USER || 'user',
		password: process.env.DB_PASS || 'password',
		database: process.env.DB_NAME || 'database_test',
		host: process.env.DB_HOST || 'localhost',
		port: Number(process.env.DB_PORT) || 5432,
		dialect: process.env.DB_DIALECT || 'postgres',
		logging: false,
	},
	production: {
		username: process.env.DB_USER || 'user',
		password: process.env.DB_PASS || 'password',
		database: process.env.DB_NAME || 'database_prod',
		host: process.env.DB_HOST || 'localhost',
		port: Number(process.env.DB_PORT) || 5432,
		dialect: process.env.DB_DIALECT || 'postgres',
		logging: false,
		dialectOptions: {
			ssl: {
				require: true,
				rejectUnauthorized: false,
			},
		},
	},
};
