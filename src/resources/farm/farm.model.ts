import { DataTypes, Model, Sequelize } from 'sequelize';
import { Farm } from './farm.schema';

type FarmCreationAttributes = Pick<Farm, 'name'>;
export class FarmModel extends Model<Farm, FarmCreationAttributes> {}

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
