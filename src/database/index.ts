import { Sequelize } from 'sequelize';
import { initUserModel, UserModel } from '../resources/user/user.model';

export interface Database {
    sequelize: Sequelize;
    models: {
        User: typeof UserModel
    }
}

export const initDatabase = async (): Promise<Database> => {
	const sequelize = new Sequelize({
		dialect: 'postgres',
		host: process.env.DB_HOST,
		port: Number(process.env.DB_PORT),
		username: process.env.DB_USER,
		password: process.env.DB_PASS,
		database: process.env.DB_NAME,
	});

	const User = initUserModel(sequelize);

	// assosiactions

	const db: Database = {
		sequelize,
		models: {
			User,
		},
	};

	// Test connection
	try {
		await sequelize.authenticate();
		console.log('Database connection established successfully.');
	} catch (error) {
		console.error('Unable to connect to the database:', error);
		throw error;
	}

	return db;
};
