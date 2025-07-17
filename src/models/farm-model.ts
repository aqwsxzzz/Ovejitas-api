import { DataTypes, Model } from 'sequelize';
import { Sequelize } from 'sequelize';

const sequelizeConfig = require('../database/sequelize-config')[process.env.NODE_ENV || 'development'];
import { FarmAttributes, FarmCreationAttributes } from '../types/farm-types';

const sequelize = new Sequelize(sequelizeConfig);

export class Farm extends Model<FarmAttributes, FarmCreationAttributes> {
	get id(): number {
		return this.getDataValue('id');
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

Farm.init(
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
