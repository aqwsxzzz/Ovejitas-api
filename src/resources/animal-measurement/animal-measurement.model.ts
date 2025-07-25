import { Model, Sequelize, DataTypes } from 'sequelize';
import { AnimalMeasurement, AnimalMeasurementType, AnimalMeasurementUnit } from './animal-measurement.schema';

type AnimalMeasurementCreationAttributes = Pick<AnimalMeasurement, 'animalId' | 'measurementType' | 'value' | 'unit' | 'measuredAt' | 'measuredBy' | 'notes'>;

export class AnimalMeasurementModel extends Model<AnimalMeasurement, AnimalMeasurementCreationAttributes> {
	declare id: number;
	declare animalId: number;
	declare measurementType: AnimalMeasurementType;
	declare value: number;
	declare unit: AnimalMeasurementUnit;
	declare measuredAt: string;
	declare measuredBy: number;
	declare notes: string;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initAnimalMeasurementModel = (sequelize: Sequelize) => AnimalMeasurementModel.init({
	id: {
		type: DataTypes.INTEGER,
		autoIncrement: true,
		primaryKey: true,
		field: 'id',
	},
	animalId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'animal_id',
		references: {
			model: 'animals',
			key: 'id',
		},
	},
	measurementType: {
		type: DataTypes.ENUM(...Object.values(AnimalMeasurementType)),
		allowNull: false,
		field: 'measurement_type',
	},
	value: {
		type: DataTypes.DECIMAL(10, 2),
		allowNull: false,
		validate: {
			min: 0,
		},
	},
	unit: {
		type: DataTypes.ENUM(...Object.values(AnimalMeasurementUnit)),
		allowNull: false,
		field: 'unit',
	},
	measuredAt: {
		type: DataTypes.DATE,
		allowNull: false,
		defaultValue: DataTypes.NOW,
		field: 'measured_at',
	},
	measuredBy: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: true,
		field: 'measured_by',
		references: {
			model: 'users',
			key: 'id',
		},
	},
	notes: {
		type: DataTypes.TEXT,
		allowNull: true,
	},
	createdAt: {
		type: DataTypes.DATE,
		allowNull: false,
		field: 'created_at',
	},
	updatedAt: {
		type: DataTypes.DATE,
		allowNull: false,
		field: 'updated_at',
	},
}, {
	sequelize,
	tableName: 'animal_measurements',
	modelName: 'AnimalMeasurement',
	timestamps: true,
	indexes: [
		{
			name: 'idx_animal_measurements_animal_type_time',
			fields: ['animal_id', 'measurement_type', 'measured_at'],
		},
		{
			name: 'idx_animal_measurements_time',
			fields: ['measured_at'],
		},
	],
});
