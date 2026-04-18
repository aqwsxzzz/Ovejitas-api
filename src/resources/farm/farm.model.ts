import { DataTypes, Model, Sequelize } from 'sequelize';
import { Farm } from './farm.schema';

type FarmCreationAttributes = Pick<Farm, 'name'> & Partial<Pick<Farm, 'latitude' | 'longitude' | 'currency'>>;
export class FarmModel extends Model<Farm, FarmCreationAttributes> {
	declare id: number;
	declare name: string;
	declare latitude: number | null;
	declare longitude: number | null;
	declare currency: string | null;
	declare createdAt: string;
	declare updatedAt: string;
}

export const initFarmModel = (sequelize: Sequelize) => FarmModel.init(
	{
		id: {
			type: DataTypes.INTEGER.UNSIGNED,
			autoIncrement: true,
			primaryKey: true,
			field: 'id',
		},
		name: {
			type: DataTypes.STRING,
			allowNull: false,
			field: 'name',
		},
		latitude: {
			type: DataTypes.DECIMAL(9, 6),
			allowNull: true,
			field: 'latitude',
		},
		longitude: {
			type: DataTypes.DECIMAL(9, 6),
			allowNull: true,
			field: 'longitude',
		},
		currency: {
			type: DataTypes.CHAR(3),
			allowNull: true,
			field: 'currency',
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
		tableName: 'farms',
		modelName: 'Farm',
		timestamps: true,
	},
);
