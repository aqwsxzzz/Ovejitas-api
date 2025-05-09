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

type UserCreationAttributes = Pick<UserAttributes, "displayName" | "email" | "password">;

export class User extends Model<UserAttributes, UserCreationAttributes> {
	get id(): number {
		return this.getDataValue("id");
	}
	get displayName(): string {
		return this.getDataValue("displayName");
	}
	get email(): string {
		return this.getDataValue("email");
	}
	get password(): string {
		return this.getDataValue("password");
	}
	get isActive(): boolean {
		return this.getDataValue("isActive");
	}
	get role(): UserRole {
		return this.getDataValue("role");
	}
	get createdAt(): Date | undefined {
		return this.getDataValue("createdAt");
	}
	get updatedAt(): Date | undefined {
		return this.getDataValue("updatedAt");
	}
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
