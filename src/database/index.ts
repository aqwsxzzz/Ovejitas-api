import {  Sequelize } from 'sequelize';
import { initUserModel, UserModel } from '../resources/user/user.model';
import { FarmModel, initFarmModel } from '../resources/farm/farm.model';
import { FarmMemberModel, initFarmMemberModel } from '../resources/farm-member/farm-member.model';
import { InvitationModel, initInvitationModel } from '../resources/invitation/invitation.model';
import { initSpeciesModel, SpeciesModel } from '../resources/species/species.model';
import {
	initSpeciesTranslationModel,
	SpeciesTranslationModel,
} from '../resources/species-translation/species-translation.model';
import { BreedModel, initBreedModel } from '../resources/breed/breed.model';
import {
	BreedTranslationModel,
	initBreedTranslationModel,
} from '../resources/breed-translation/breed-translation.model';
import { AnimalModel, initAnimalModel } from '../resources/animal/animal.model';
import {
	AnimalMeasurementModel,
	initAnimalMeasurementModel,
} from '../resources/animal-measurement/animal-measurement.model';
import {
	FinancialTransactionModel,
	initFinancialTransactionModel,
} from '../resources/financial-transaction/financial-transaction.model';
import { FlockModel, initFlockModel } from '../resources/flock/flock.model';
import { FlockEventModel, initFlockEventModel } from '../resources/flock-event/flock-event.model';
import {
	EggCollectionModel,
	initEggCollectionModel,
} from '../resources/egg-collection/egg-collection.model';
import { FeedTypeModel, initFeedTypeModel } from '../resources/feed-type/feed-type.model';
import { FeedLotModel, initFeedLotModel } from '../resources/feed-lot/feed-lot.model';
import { FeedConsumptionModel, initFeedConsumptionModel } from '../resources/feed-consumption/feed-consumption.model';
import {
	FeedConsumptionLotModel,
	initFeedConsumptionLotModel,
} from '../resources/feed-consumption/feed-consumption-lot.model';

export interface Database {
	sequelize: Sequelize;
	models: {
		User: typeof UserModel;
		Farm: typeof FarmModel;
		FarmMember: typeof FarmMemberModel;
		Invitation: typeof InvitationModel;
		Species: typeof SpeciesModel;
		SpeciesTranslation: typeof SpeciesTranslationModel;
		Breed: typeof BreedModel;
		BreedTranslation: typeof BreedTranslationModel;
		Animal: typeof AnimalModel;
		AnimalMeasurement: typeof AnimalMeasurementModel;
		FinancialTransaction: typeof FinancialTransactionModel;
		Flock: typeof FlockModel;
		FlockEvent: typeof FlockEventModel;
		EggCollection: typeof EggCollectionModel;
		FeedType: typeof FeedTypeModel;
		FeedLot: typeof FeedLotModel;
		FeedConsumption: typeof FeedConsumptionModel;
		FeedConsumptionLot: typeof FeedConsumptionLotModel;
	};
}

export const initDatabase = async (): Promise<Database> => {
	const isProduction = process.env.NODE_ENV === 'production';

	const sequelize = new Sequelize({
		dialect: 'postgres',
		host: process.env.DB_HOST,
		port: Number(process.env.DB_PORT),
		username: process.env.DB_USER,
		password: process.env.DB_PASS,
		database: process.env.DB_NAME,
		logging: false,
		pool: {
			max: 5,
			min: 0,
			acquire: 30000,
			idle: 10000,
		},
		...(isProduction && {
			dialectOptions: {
				ssl: {
					require: true,
					rejectUnauthorized: false,
				},
			},
		}),
	});

	const User = initUserModel(sequelize);
	const Farm = initFarmModel(sequelize);
	const FarmMember = initFarmMemberModel(sequelize);
	const Invitation = initInvitationModel(sequelize);
	const SpeciesTranslation = initSpeciesTranslationModel(sequelize);
	const Species = initSpeciesModel(sequelize);
	const Breed = initBreedModel(sequelize);
	const BreedTranslation = initBreedTranslationModel(sequelize);
	const Animal = initAnimalModel(sequelize);
	const AnimalMeasurement = initAnimalMeasurementModel(sequelize);
	const FinancialTransaction = initFinancialTransactionModel(sequelize);
	const Flock = initFlockModel(sequelize);
	const FlockEvent = initFlockEventModel(sequelize);
	const EggCollection = initEggCollectionModel(sequelize);
	const FeedType = initFeedTypeModel(sequelize);
	const FeedLot = initFeedLotModel(sequelize);
	const FeedConsumption = initFeedConsumptionModel(sequelize);
	const FeedConsumptionLot = initFeedConsumptionLotModel(sequelize);

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

	// Breed & BreedTranslation
	Breed.hasMany(BreedTranslation, { foreignKey: 'breedId', as: 'translations' });
	BreedTranslation.belongsTo(Breed, { foreignKey: 'breedId', as: 'breed' });

	// Animal associations
	Animal.belongsTo(FarmModel, { foreignKey: 'farmId', as: 'farm' });
	Animal.belongsTo(Species, { foreignKey: 'speciesId', as: 'species' });
	Animal.belongsTo(Breed, { foreignKey: 'breedId', as: 'breed' });
	Animal.belongsTo(Animal, { foreignKey: 'fatherId', as: 'father' });
	Animal.belongsTo(Animal, { foreignKey: 'motherId', as: 'mother' });
	Animal.hasMany(Animal, { foreignKey: 'fatherId', as: 'fatheredChildren' });

	// AnimalMeasurement associations
	AnimalMeasurement.belongsTo(Animal, { foreignKey: 'animalId', as: 'animal' });
	AnimalMeasurement.belongsTo(UserModel, { foreignKey: 'measuredBy', as: 'measurer' });
	Animal.hasMany(AnimalMeasurement, { foreignKey: 'animalId', as: 'measurements' });

	// FinancialTransaction associations
	FinancialTransaction.belongsTo(FarmModel, { foreignKey: 'farmId', as: 'farm' });
	FinancialTransaction.belongsTo(Species, { foreignKey: 'speciesId', as: 'species' });
	FinancialTransaction.belongsTo(UserModel, { foreignKey: 'createdBy', as: 'creator' });
	FarmModel.hasMany(FinancialTransaction, { foreignKey: 'farmId', as: 'financialTransactions' });

	// Flock associations
	Flock.belongsTo(FarmModel, { foreignKey: 'farmId', as: 'farm' });
	Flock.belongsTo(Species, { foreignKey: 'speciesId', as: 'species' });
	Flock.belongsTo(Breed, { foreignKey: 'breedId', as: 'breed' });
	FarmModel.hasMany(Flock, { foreignKey: 'farmId', as: 'flocks' });
	Species.hasMany(Flock, { foreignKey: 'speciesId', as: 'flocks' });
	Breed.hasMany(Flock, { foreignKey: 'breedId', as: 'flocksByBreed' });

	// FlockEvent associations
	FlockEvent.belongsTo(Flock, { foreignKey: 'flockId', as: 'flock' });
	FlockEvent.belongsTo(UserModel, { foreignKey: 'recordedBy', as: 'recorder' });
	Flock.hasMany(FlockEvent, { foreignKey: 'flockId', as: 'events' });

	// EggCollection associations
	EggCollection.belongsTo(Flock, { foreignKey: 'flockId', as: 'flock' });
	EggCollection.belongsTo(UserModel, { foreignKey: 'collectedBy', as: 'collector' });
	Flock.hasMany(EggCollection, { foreignKey: 'flockId', as: 'eggCollections' });

	// Feed inventory associations
	FeedType.belongsTo(FarmModel, { foreignKey: 'farmId', as: 'farm' });
	FarmModel.hasMany(FeedType, { foreignKey: 'farmId', as: 'feedTypes' });

	FeedLot.belongsTo(FarmModel, { foreignKey: 'farmId', as: 'farm' });
	FeedLot.belongsTo(FeedType, { foreignKey: 'feedTypeId', as: 'feedType' });
	FeedLot.belongsTo(UserModel, { foreignKey: 'createdBy', as: 'creator' });
	FeedType.hasMany(FeedLot, { foreignKey: 'feedTypeId', as: 'lots' });
	FarmModel.hasMany(FeedLot, { foreignKey: 'farmId', as: 'feedLots' });

	FeedConsumption.belongsTo(FarmModel, { foreignKey: 'farmId', as: 'farm' });
	FeedConsumption.belongsTo(Flock, { foreignKey: 'flockId', as: 'flock' });
	FeedConsumption.belongsTo(FeedType, { foreignKey: 'feedTypeId', as: 'feedType' });
	FeedConsumption.belongsTo(UserModel, { foreignKey: 'createdBy', as: 'creator' });
	FeedConsumption.hasMany(FeedConsumptionLot, { foreignKey: 'consumptionId', as: 'lots' });
	Flock.hasMany(FeedConsumption, { foreignKey: 'flockId', as: 'feedConsumptions' });
	FeedType.hasMany(FeedConsumption, { foreignKey: 'feedTypeId', as: 'consumptions' });

	FeedConsumptionLot.belongsTo(FeedConsumption, { foreignKey: 'consumptionId', as: 'consumption' });
	FeedConsumptionLot.belongsTo(FeedLot, { foreignKey: 'lotId', as: 'lot' });
	FeedLot.hasMany(FeedConsumptionLot, { foreignKey: 'lotId', as: 'consumptionLots' });

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
			BreedTranslation,
			Animal,
			AnimalMeasurement,
			FinancialTransaction,
			Flock,
			FlockEvent,
			EggCollection,
			FeedType,
			FeedLot,
			FeedConsumption,
			FeedConsumptionLot,
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
