import { DataTypes, Model, Sequelize } from 'sequelize';
import { BreedTranslation } from './breed-translation.schema';
import { UserLanguage } from '../user/user.schema';

type BreedTranslationCreationAttributes = Pick<BreedTranslation, 'breedId' | 'language' | 'name'>;

export class BreedTranslationModel extends Model<BreedTranslation, BreedTranslationCreationAttributes> {
	declare id: number;
	declare breedId: number;
	declare language: UserLanguage;
	declare name: string;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initBreedTranslationModel = (sequelize: Sequelize) => BreedTranslationModel.init({
	id: {
		type: DataTypes.INTEGER.UNSIGNED,
		autoIncrement: true,
		primaryKey: true,
		field: 'id',
	},
	breedId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'breed_id',
		references: {
			model: 'breeds',
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
	tableName: 'breed_translation',
	modelName: 'BreedTranslation',
	timestamps: true,
});
