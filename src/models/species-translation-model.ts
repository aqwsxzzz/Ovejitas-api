import { DataTypes, Model } from 'sequelize';
import { Sequelize } from 'sequelize';

const sequelizeConfig = require('../database/sequelize-config')[process.env.NODE_ENV || 'development'];

const sequelize = new Sequelize(sequelizeConfig);
import { SpeciesTranslationAttributes, SpeciesTranslationCreationAttributes } from '../types/species-translation-types';
import { UserLanguage } from './user-model';

export class SpeciesTranslation extends Model<SpeciesTranslationAttributes, SpeciesTranslationCreationAttributes> {
	get id(): number {
		return this.getDataValue('id');
	}
	get speciesId(): number {
		return this.getDataValue('speciesId');
	}
	get languageCode(): string {
		return this.getDataValue('languageCode');
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

SpeciesTranslation.init(
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
		languageCode: {
			type: DataTypes.ENUM(...Object.values(UserLanguage)),
			allowNull: false,
			field: 'language_code',
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
		tableName: 'species_translation',
		modelName: 'SpeciesTranslation',
		timestamps: true,
		indexes: [
			{
				unique: true,
				fields: ['speciesId', 'name'],
			},
			{
				unique: true,
				fields: ['name', 'languageCode'],
			},
		],
	},
);
