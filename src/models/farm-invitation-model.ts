import { DataTypes, Model } from "sequelize";
import { Sequelize } from "sequelize";
// eslint-disable-next-line @typescript-eslint/no-var-requires
const sequelizeConfig = require("../config/sequelize-config")[process.env.NODE_ENV || "development"];
import { FarmInvitationAttributes, FarmInvitationCreationAttributes, FarmInvitationStatus } from "../types/farm-invitation-types";
import { FarmMemberRole, FarmMemberRoleEnum } from "../types/farm-members-types";

const sequelize = new Sequelize(sequelizeConfig);

export class FarmInvitation extends Model<FarmInvitationAttributes, FarmInvitationCreationAttributes> {
	get id(): string {
		return this.getDataValue("id");
	}
	get email(): string {
		return this.getDataValue("email");
	}
	get farmId(): string {
		return this.getDataValue("farmId");
	}
	get role(): FarmMemberRole {
		return this.getDataValue("role");
	}
	get token(): string {
		return this.getDataValue("token");
	}
	get status(): FarmInvitationStatus {
		return this.getDataValue("status");
	}
	get createdAt(): string | undefined {
		return this.getDataValue("createdAt");
	}
	get updatedAt(): string | undefined {
		return this.getDataValue("updatedAt");
	}
	get expiresAt(): Date | undefined {
		return this.getDataValue("expiresAt");
	}
}

FarmInvitation.init(
	{
		id: {
			type: DataTypes.INTEGER.UNSIGNED,
			autoIncrement: true,
			primaryKey: true,
			field: "id",
		},
		email: {
			type: DataTypes.STRING,
			allowNull: false,
			field: "email",
		},
		farmId: {
			type: DataTypes.INTEGER.UNSIGNED,
			allowNull: false,
			field: "farm_id",
		},
		role: {
			type: DataTypes.ENUM(...Object.values(FarmMemberRoleEnum)),
			allowNull: false,
			defaultValue: FarmMemberRoleEnum.MEMBER,
			field: "role",
		},
		token: {
			type: DataTypes.STRING,
			allowNull: false,
			unique: true,
			field: "token",
		},
		status: {
			type: DataTypes.ENUM("pending", "accepted", "expired", "cancelled"),
			allowNull: false,
			defaultValue: "pending",
			field: "status",
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
		expiresAt: {
			type: DataTypes.DATE,
			allowNull: true,
			field: "expires_at",
		},
	},
	{
		sequelize,
		tableName: "farm_invitations",
		modelName: "FarmInvitation",
		timestamps: true,
	}
);
