import { DataTypes, Model, Sequelize } from 'sequelize';
import { FarmMember, FarmMemberRole } from './farm-member.schema';

type FarmMemberCreationAttributes = Pick<FarmMember, 'farmId' | 'userId' | 'role'>;

export class FarmMemberModel extends Model<FarmMember, FarmMemberCreationAttributes> { }

export const initFarmMemberModel = (sequelize: Sequelize) => FarmMemberModel.init({
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
		type: DataTypes.ENUM(FarmMemberRole.OWNER, FarmMemberRole.MEMBER),
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
