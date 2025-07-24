import { DataTypes, Model, Sequelize } from 'sequelize';
import { Breed } from './breed.schema';

type BreedCreationAttributes = Omit<Breed, 'id' | 'createdAt' | 'updatedAt'>;

export class BreedModel extends Model<Breed, BreedCreationAttributes> {
	declare id: number;
	declare speciesId: number;
	declare name: string;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initBreedModel = (sequelize: Sequelize) => BreedModel.init({
	id: {
		type: DataTypes.INTEGER.UNSIGNED,
		autoIncrement: true,
		primaryKey: true,
		field: 'id',
	},
	speciesId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'species_id',
		references: {
			model: 'species',
			key: 'id',
		},
		onDelete: 'CASCADE',
	},
	name: {
		type: DataTypes.STRING,
		allowNull: false,
		field: 'name',
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
	tableName: 'breeds',
	modelName: 'Breed',
	timestamps: true,
	indexes: [
		{
			unique: true,
			fields: ['species_id', 'name'],
		},
	],
});
