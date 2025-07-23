import { DataTypes, Model, Sequelize } from 'sequelize';
import { SpeciesTranslation } from './species-translation.schema';
import { UserLanguage } from '../user/user.schema';

type SpeciesTranslationCreationAttributes = Pick<SpeciesTranslation, 'speciesId' | 'language' | 'name'>;

export class SpeciesTranslationModel extends Model<SpeciesTranslation, SpeciesTranslationCreationAttributes> {
	declare id: number;
	declare speciesId: number;
	declare languageCode: UserLanguage;
	declare name: string;
	declare createdAt: Date;
	declare updatedAt: Date;
}

export const initSpeciesTranslationModel = (sequelize: Sequelize) => SpeciesTranslationModel.init({
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
	language: {
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
}, {
	sequelize,
	tableName: 'species_translation',
	modelName: 'SpeciesTranslation',
	timestamps: true,
});
