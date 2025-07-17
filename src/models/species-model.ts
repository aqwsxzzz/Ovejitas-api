import { DataTypes, Model, Association } from 'sequelize';
import { Sequelize } from 'sequelize';

const sequelizeConfig = require('../database/sequelize-config')[process.env.NODE_ENV || 'development'];
import { SpeciesTranslation } from './species-translation-model';
import { SpeciesAttributes, SpeciesCreationAttributes } from '../types/species-types';

const sequelize = new Sequelize(sequelizeConfig);

export class Species extends Model<SpeciesAttributes, SpeciesCreationAttributes> {
	get id(): number {
		return this.getDataValue('id');
	}
	get createdAt(): Date | undefined {
		return this.getDataValue('createdAt');
	}
	get updatedAt(): Date | undefined {
		return this.getDataValue('updatedAt');
	}
	public static associations: {
		translations: Association<Species, SpeciesTranslation>;
	};
}

Species.init(
	{
		id: {
			type: DataTypes.INTEGER.UNSIGNED,
			autoIncrement: true,
			primaryKey: true,
			field: 'id',
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
		tableName: 'species',
		modelName: 'Species',
		timestamps: true,
	},
);
