import { DataTypes, Model, Optional, Sequelize } from 'sequelize';
import { User } from './user.schema';

export enum UserRole {
    USER = 'user',
    ADMIN = 'admin',
}

export enum UserLanguage {
    EN = 'en',
    ES = 'es',
}

type UserCreationAttributes = Optional<User, 'id' | 'createdAt' | 'updatedAt' | 'lastVisitedFarmId' | 'isActive' | 'role' | 'language'>;

export class UserModel extends Model<User, UserCreationAttributes> {}

export const initUserModel = (sequelize: Sequelize ) => UserModel.init(
	{
		id: {
			type: DataTypes.INTEGER.UNSIGNED,
			autoIncrement: true,
			primaryKey: true,
			field: 'id',
		},
		displayName: {
			type: DataTypes.STRING,
			allowNull: false,
			field: 'display_name',
		},
		email: {
			type: DataTypes.STRING,
			allowNull: false,
			unique: true,
			validate: {
				isEmail: true,
			},
			field: 'email',
		},
		password: {
			type: DataTypes.STRING,
			allowNull: false,
			field: 'password',
		},
		isActive: {
			type: DataTypes.BOOLEAN,
			allowNull: false,
			defaultValue: true,
			field: 'is_active',
		},
		role: {
			type: DataTypes.ENUM(...Object.values(UserRole)),
			allowNull: false,
			defaultValue: UserRole.USER,
			field: 'role',
		},
		language: {
			type: DataTypes.ENUM(...Object.values(UserLanguage)),
			allowNull: false,
			defaultValue: UserLanguage.EN,
			field: 'language',
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
		lastVisitedFarmId: {
			type: DataTypes.INTEGER.UNSIGNED,
			allowNull: true,
			field: 'last_visited_farm_id',
		},
	},
	{
		sequelize,
		tableName: 'users',
		modelName: 'User',
		timestamps: true,
	},
);
