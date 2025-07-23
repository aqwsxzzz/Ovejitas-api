import { DataTypes, Model, Optional, Sequelize } from 'sequelize';
import { InvitationStatus, Invitation } from './invitation.schema';
import { FarmModel } from '../farm/farm.model';
import { FarmMemberRole } from '../farm-member/farm-member.schema';

type InvitationCreationAttributes = Optional<Invitation, 'id' | 'createdAt' | 'updatedAt' | 'expiresAt'>;

export class InvitationModel extends Model<Invitation, InvitationCreationAttributes> { }

export const initInvitationModel = (sequelize: Sequelize) => InvitationModel.init({
	id: {
		type: DataTypes.INTEGER,
		autoIncrement: true,
		primaryKey: true,
		field: 'id',
	},

	email: {
		type: DataTypes.STRING,
		allowNull: false,
		field: 'email',
	},
	farmId: {
		type: DataTypes.INTEGER.UNSIGNED,
		allowNull: false,
		field: 'farm_id',
		references: {
			model: FarmModel,
			key: 'id',
		},
		onDelete: 'CASCADE',
	},
	role: {
		type: DataTypes.ENUM(...Object.values(FarmMemberRole)),
		allowNull: false,
		defaultValue: FarmMemberRole.MEMBER,
		field: 'role',
	},
	token: {
		type: DataTypes.STRING,
		allowNull: false,
		field: 'token',
		unique: true,
	},
	status: {
		type: DataTypes.ENUM(...Object.values(InvitationStatus)),
		allowNull: false,
		defaultValue: InvitationStatus.PENDING,
		field: 'status',
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
	expiresAt: {
		type: DataTypes.DATE,
		allowNull: false,
		field: 'expires_at',
	},
}, {
	sequelize,
	tableName: 'farm_invitations',
	modelName: 'Invitation',
	timestamps: true,
});
