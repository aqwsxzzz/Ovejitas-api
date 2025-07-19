import { DataTypes, Model, Optional, Sequelize } from 'sequelize';
import { Invitation } from './invitation.schema';
import { FarmModel } from '../farm/farm.model';
import { FarmMemberRole } from '../farm-member/farm-member.model';

export enum FarmInvitationStatus {
	PENDING = 'pending',
	ACCEPTED = 'accepted',
	EXPIRED = 'expired',
	CANCELLED = 'cancelled',
}

type FarmInvitationCreationAttributes = Optional<Invitation, 'id' | 'createdAt' | 'updatedAt' | 'expiresAt'>;

export class FarmInvitationModel extends Model<Invitation, FarmInvitationCreationAttributes> { }

export const initFarmInvitationModel = (sequelize: Sequelize) => FarmInvitationModel.init({
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
		type: DataTypes.ENUM(...Object.values(FarmInvitationStatus)),
		allowNull: false,
		defaultValue: FarmInvitationStatus.PENDING,
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
	modelName: 'FarmInvitation',
	timestamps: true,
});
