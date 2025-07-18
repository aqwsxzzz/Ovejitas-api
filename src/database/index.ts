import { Sequelize } from 'sequelize';
import { initUserModel, UserModel } from '../resources/user/user.model';
import { FarmModel, initFarmModel } from '../resources/farm/farm.model';
import { FarmMemberModel, initFarmMemberModel } from '../resources/farm-member/farm-member.model';

export interface Database {
    sequelize: Sequelize;
    models: {
		User: typeof UserModel
		Farm: typeof FarmModel
		FarmMember: typeof FarmMemberModel
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
	const Farm = initFarmModel(sequelize);
	const FarmMember = initFarmMemberModel(sequelize);

	// assosiactions
	// Farm & FarmMembers
	FarmMemberModel.belongsTo(FarmModel, { foreignKey: 'farmId', as: 'farm' });
	FarmMemberModel.belongsTo(UserModel, { foreignKey: 'userId', as: 'user' });
	FarmModel.hasMany(FarmMemberModel, { foreignKey: 'farmId', as: 'members' });
	UserModel.hasMany(FarmMemberModel, { foreignKey: 'userId', as: 'farmMemberships' });

	const db: Database = {
		sequelize,
		models: {
			User,
			Farm,
			FarmMember,
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
