import { DataTypes, Model, Optional } from "sequelize";
import { Sequelize } from "sequelize";
// eslint-disable-next-line @typescript-eslint/no-var-requires
const sequelizeConfig = require("../config/sequelize-config")[process.env.NODE_ENV || "development"];

const sequelize = new Sequelize(sequelizeConfig);

export enum UserRole {
	USER = "user",
	ADMIN = "admin",
}

interface UserAttributes {
	id: number;
	displayName: string;
	email: string;
	password: string;
	isActive: boolean;
	role: UserRole;
	createdAt?: Date;
	updatedAt?: Date;
}

interface UserCreationAttributes extends Optional<UserAttributes, "id" | "isActive" | "role" | "createdAt" | "updatedAt"> {}

export class User extends Model<UserAttributes, UserCreationAttributes> implements UserAttributes {
	public id!: number;
	public displayName!: string;
	public email!: string;
	public password!: string;
	public isActive!: boolean;
	public role!: UserRole;
	public readonly createdAt!: Date;
	public readonly updatedAt!: Date;
}

User.init(
	{
		id: {
			type: DataTypes.INTEGER.UNSIGNED,
			autoIncrement: true,
			primaryKey: true,
			field: "id",
		},
		displayName: {
			type: DataTypes.STRING,
			allowNull: false,
			field: "display_name",
		},
		email: {
			type: DataTypes.STRING,
			allowNull: false,
			unique: true,
			validate: {
				isEmail: true,
			},
			field: "email",
		},
		password: {
			type: DataTypes.STRING,
			allowNull: false,
			field: "password",
		},
		isActive: {
			type: DataTypes.BOOLEAN,
			allowNull: false,
			defaultValue: true,
			field: "is_active",
		},
		role: {
			type: DataTypes.ENUM(...Object.values(UserRole)),
			allowNull: false,
			defaultValue: UserRole.USER,
			field: "role",
		},
		createdAt: {
			type: DataTypes.DATE,
			allowNull: false,
			defaultValue: DataTypes.NOW,
			field: "created_at",
		},
		updatedAt: {
			type: DataTypes.DATE,
			allowNull: false,
			defaultValue: DataTypes.NOW,
			field: "updated_at",
		},
	},
	{
		sequelize,
		tableName: "users",
		modelName: "User",
		timestamps: true,
	}
);
