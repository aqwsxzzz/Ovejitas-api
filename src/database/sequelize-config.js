// eslint-disable-next-line @typescript-eslint/no-require-imports
require('dotenv').config();

module.exports = {
	development: {
		use_env_variable: 'DATABASE_URL',
		dialect: 'postgres',
		logging: process.env.NODE_ENV !== 'production',
		dialectOptions: process.env.DATABASE_URL?.includes('supabase')
			? { ssl: { require: true, rejectUnauthorized: false } }
			: {},
	},
	test: {
		dialect: 'postgres',
		username: process.env.DB_USER || 'user',
		password: process.env.DB_PASS || 'password',
		database: process.env.DB_NAME || 'database_test',
		host: process.env.DB_HOST || 'localhost',
		logging: false,
	},
	production: {
		use_env_variable: 'DATABASE_URL',
		dialect: 'postgres',
		logging: false,
		dialectOptions: { ssl: { require: true, rejectUnauthorized: false } },
	},
};
