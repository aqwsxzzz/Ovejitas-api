import { Sequelize } from 'sequelize';
import { initUserModel, UserModel } from '../resources/user/user.model';
import { FarmModel, initFarmModel } from '../resources/farm/farm.model';
import { FarmMemberModel, initFarmMemberModel } from '../resources/farm-member/farm-member.model';
import { InvitationModel, initInvitationModel } from '../resources/invitation/invitation.model';
import { initSpeciesModel, SpeciesModel } from '../resources/species/species.model';
import { initSpeciesTranslationModel, SpeciesTranslationModel } from '../resources/species-translation/species-translation.model';
import { BreedModel, initBreedModel } from '../resources/breed/breed.model';

export interface Database {
    sequelize: Sequelize;
    models: {
		User: typeof UserModel
		Farm: typeof FarmModel
		FarmMember: typeof FarmMemberModel
		Invitation: typeof InvitationModel
		Species: typeof SpeciesModel
		SpeciesTranslation: typeof SpeciesTranslationModel
		Breed: typeof BreedModel
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
	const Invitation = initInvitationModel(sequelize);
	const SpeciesTranslation = initSpeciesTranslationModel(sequelize);
	const Species = initSpeciesModel(sequelize);
	const Breed = initBreedModel(sequelize);

	// associations
	// Farm & FarmMembers
	FarmMemberModel.belongsTo(FarmModel, { foreignKey: 'farmId', as: 'farm' });
	FarmMemberModel.belongsTo(UserModel, { foreignKey: 'userId', as: 'user' });
	FarmModel.hasMany(FarmMemberModel, { foreignKey: 'farmId', as: 'members' });
	UserModel.hasMany(FarmMemberModel, { foreignKey: 'userId', as: 'farmMemberships' });

	// Species & SpeciesTranslation
	Species.hasMany(SpeciesTranslation, { foreignKey: 'speciesId', as: 'translations' });
	SpeciesTranslation.belongsTo(Species, { foreignKey: 'speciesId', as: 'species' });

	// Breed & Species
	Species.hasMany(Breed, { foreignKey: 'speciesId', as: 'breeds' });
	Breed.belongsTo(Species, { foreignKey: 'speciesId', as: 'species' });

	const db: Database = {
		sequelize,
		models: {
			User,
			Farm,
			FarmMember,
			Invitation,
			Species,
			SpeciesTranslation,
			Breed,
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
