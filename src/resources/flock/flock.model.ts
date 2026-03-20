import { DataTypes, Model, Sequelize } from 'sequelize';
import { Flock, FlockAcquisitionType, FlockStatus, FlockType } from './flock.schema';

type FlockCreationAttributes = Pick<Flock, 'farmId' | 'speciesId' | 'breedId' | 'name' | 'flockType' | 'initialCount' | 'currentCount' | 'startDate' | 'acquisitionType'> & Partial<Pick<Flock, 'status' | 'endDate' | 'houseName' | 'ageAtAcquisitionWeeks' | 'notes'>>;

export class FlockModel extends Model<Flock, FlockCreationAttributes> {
	declare id: number;
	declare farmId: number;
	declare speciesId: number;
	declare breedId: number;
	declare name: string;
	declare flockType: string;
	declare initialCount: number;
	declare currentCount: number;
	declare status: string;
	declare startDate: string;
	declare endDate: string | null;
	declare houseName: string | null;
	declare acquisitionType: string;
	declare ageAtAcquisitionWeeks: number | null;
	declare notes: string | null;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initFlockModel = (sequelize: Sequelize) => FlockModel.init({
	id: {
		type: DataTypes.INTEGER.UNSIGNED,
		autoIncrement: true,
		primaryKey: true,
		field: 'id',
	},
	farmId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'farm_id',
		references: { model: 'farms', key: 'id' },
		onDelete: 'CASCADE',
	},
	speciesId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'species_id',
		references: { model: 'species', key: 'id' },
		onDelete: 'CASCADE',
	},
	breedId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'breed_id',
		references: { model: 'breeds', key: 'id' },
		onDelete: 'CASCADE',
	},
	name: {
		type: DataTypes.STRING,
		allowNull: false,
		field: 'name',
	},
	flockType: {
		type: DataTypes.ENUM(...Object.values(FlockType)),
		allowNull: false,
		field: 'flock_type',
	},
	initialCount: {
		type: DataTypes.INTEGER,
		allowNull: false,
		field: 'initial_count',
	},
	currentCount: {
		type: DataTypes.INTEGER,
		allowNull: false,
		field: 'current_count',
	},
	status: {
		type: DataTypes.ENUM(...Object.values(FlockStatus)),
		allowNull: false,
		field: 'status',
		defaultValue: FlockStatus.Active,
	},
	startDate: {
		type: DataTypes.DATEONLY,
		allowNull: false,
		field: 'start_date',
	},
	endDate: {
		type: DataTypes.DATEONLY,
		allowNull: true,
		field: 'end_date',
	},
	houseName: {
		type: DataTypes.STRING,
		allowNull: true,
		field: 'house_name',
	},
	acquisitionType: {
		type: DataTypes.ENUM(...Object.values(FlockAcquisitionType)),
		allowNull: false,
		field: 'acquisition_type',
	},
	ageAtAcquisitionWeeks: {
		type: DataTypes.INTEGER,
		allowNull: true,
		field: 'age_at_acquisition_weeks',
	},
	notes: {
		type: DataTypes.TEXT,
		allowNull: true,
	},
	createdAt: {
		type: DataTypes.DATE,
		allowNull: false,
		defaultValue: DataTypes.NOW,
		field: 'created_at',
	},
	updatedAt: {
		type: DataTypes.DATE,
		allowNull: false,
		defaultValue: DataTypes.NOW,
		field: 'updated_at',
	},
}, {
	sequelize,
	tableName: 'flocks',
	modelName: 'Flock',
	timestamps: true,
	indexes: [
		{
			unique: true,
			fields: ['farm_id', 'name'],
			name: 'idx_flocks_farm_name_unique',
		},
		{
			fields: ['farm_id', 'status'],
			name: 'idx_flocks_farm_status',
		},
		{
			fields: ['farm_id', 'species_id'],
			name: 'idx_flocks_farm_species',
		},
	],
});
