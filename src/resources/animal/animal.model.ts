import { DataTypes, Model, Sequelize } from 'sequelize';
import { Animal, AnimalAcquisitionType, AnimalReproductiveStatus, AnimalSex, AnimalStatus } from './animal.schema';

type AnimalCreationAttributes = Pick<Animal, 'name' | 'speciesId' | 'farmId' | 'breedId' | 'tagNumber' > & Partial<Pick<Animal, 'sex' | 'birthDate' | 'weightId' | 'status' | 'reproductiveStatus' | 'fatherId' | 'motherId' | 'acquisitionType' | 'acquisitionDate'>>;

export class AnimalModel extends Model<Animal, AnimalCreationAttributes> {
	declare id: number;
	declare farmId: number;
	declare speciesId: number;
	declare breedId: number;
	declare name: string;
	declare tagNumber: string;
	declare sex: string;
	declare birthDate: string;
	declare status: string;
	declare reproductiveStatus: string;
	declare fatherId: number | null | undefined;
	declare motherId: number | null | undefined;
	declare acquisitionType: string;
	declare acquisitionDate: string;
	declare createdAt: string;
	declare updatedAt: string;
	declare weightId: number | null | undefined;
	declare groupName: string;
}

export const initAnimalModel = (sequelize: Sequelize) => AnimalModel.init({
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
		allowNull: true,
		field: 'name',
	},
	tagNumber: {
		type: DataTypes.STRING,
		allowNull: false,
		field: 'tag_number',
	},
	sex: {
		type: DataTypes.ENUM(...Object.values(AnimalSex)),
		allowNull: false,
		field: 'sex',
		defaultValue: AnimalSex.Unknown,
	},
	birthDate: {
		type: DataTypes.DATE,
		allowNull: true,
		field: 'birth_date',
	},

	groupName: {
		type: DataTypes.STRING,
		allowNull: true,
		field: 'group_name',
	},

	status: {
		type: DataTypes.ENUM(...Object.values(AnimalStatus)),
		allowNull: false,
		field: 'status',
		defaultValue: AnimalStatus.Alive,
	},
	reproductiveStatus: {
		type: DataTypes.ENUM(...Object.values(AnimalReproductiveStatus)),
		allowNull: false,
		field: 'reproductive_status',
		defaultValue: AnimalReproductiveStatus.Other,
	},

	fatherId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: true,
		field: 'father_id',
		references: { model: 'animals', key: 'id' },
		onDelete: 'SET NULL',
	},
	motherId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: true,
		field: 'mother_id',
		references: { model: 'animals', key: 'id' },
		onDelete: 'SET NULL',
	},
	acquisitionType: {
		type: DataTypes.ENUM(...Object.values(AnimalAcquisitionType)),
		allowNull: true,
		field: 'acquisition_type',
		defaultValue: AnimalAcquisitionType.Other,
	},
	acquisitionDate: {
		type: DataTypes.DATE,
		allowNull: true,
		field: 'acquisition_date',
	},
	weightId: {
		type: DataTypes.INTEGER,
		allowNull: true,
		field: 'weight_id',
		references: { model: 'animal_measurements', key: 'id' },
		onDelete: 'SET NULL',
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
	tableName: 'animals',
	modelName: 'Animal',
	timestamps: true,
	indexes: [
		{
			unique: true,
			fields: ['farm_id', 'species_id', 'tag_number'],
			where: { tag_number: { $ne: null } },
		},
	],
});
