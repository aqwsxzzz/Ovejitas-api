import { DataTypes, Model, Optional } from "sequelize";
import { Sequelize } from "sequelize";
// eslint-disable-next-line @typescript-eslint/no-var-requires
const sequelizeConfig = require("../config/sequelize-config")[process.env.NODE_ENV || "development"];
import { UserAttributes, UserCreationAttributes } from "../types/user-types";

const sequelize = new Sequelize(sequelizeConfig);

export enum UserRole {
	USER = "user",
	ADMIN = "admin",
}

export enum UserLanguage {
	EN = "en",
	ES = "es",
}

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
	get language(): UserLanguage {
		return this.getDataValue("language");
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
		language: {
			type: DataTypes.ENUM(...Object.values(UserLanguage)),
			allowNull: false,
			defaultValue: UserLanguage.EN,
			field: "language",
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
