import { DataTypes, Model } from 'sequelize';
import { Sequelize } from 'sequelize';

const sequelizeConfig = require('../database/sequelize-config')[process.env.NODE_ENV || 'development'];

import { FarmMembersAttributes, FarmMembersCreationAttributes, FarmMemberRole } from '../types/farm-members-types';

const sequelize = new Sequelize(sequelizeConfig);

export class FarmMembers extends Model<FarmMembersAttributes, FarmMembersCreationAttributes> {
	get id(): number {
		return this.getDataValue('id');
	}
	get farmId(): number {
		return this.getDataValue('farmId');
	}
	get userId(): number {
		return this.getDataValue('userId');
	}
	get role(): FarmMemberRole {
		return this.getDataValue('role');
	}
	get createdAt(): Date | undefined {
		return this.getDataValue('createdAt');
	}
	get updatedAt(): Date | undefined {
		return this.getDataValue('updatedAt');
	}
}

FarmMembers.init(
	{
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
		},
		userId: {
			type: DataTypes.INTEGER.UNSIGNED,
			allowNull: false,
			field: 'user_id',
		},
		role: {
			type: DataTypes.ENUM('owner', 'member'),
			allowNull: false,
			defaultValue: 'member',
			field: 'role',
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
		tableName: 'farm_members',
		modelName: 'FarmMembers',
		timestamps: true,
	},
);
