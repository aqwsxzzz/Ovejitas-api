import { DataTypes, Model } from 'sequelize';
import { Sequelize } from 'sequelize';

const sequelizeConfig = require('../database/sequelize-config')[process.env.NODE_ENV || 'development'];
import { BreedAttributes, BreedCreationAttributes } from '../types/breed-types';

const sequelize = new Sequelize(sequelizeConfig);

export class Breed extends Model<BreedAttributes, BreedCreationAttributes> {
	get id(): number {
		return this.getDataValue('id');
	}
	get speciesId(): number {
		return this.getDataValue('speciesId');
	}
	get name(): string {
		return this.getDataValue('name');
	}
	get createdAt(): Date | undefined {
		return this.getDataValue('createdAt');
	}
	get updatedAt(): Date | undefined {
		return this.getDataValue('updatedAt');
	}
}

Breed.init(
	{
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
	},
	{
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
	},
);
