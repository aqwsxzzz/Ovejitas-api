import { DataTypes, Model } from "sequelize";
import { Sequelize } from "sequelize";
// eslint-disable-next-line @typescript-eslint/no-var-requires
const sequelizeConfig = require("../config/sequelize-config")[process.env.NODE_ENV || "development"];

const sequelize = new Sequelize(sequelizeConfig);

export interface SpeciesAttributes {
	id: number;
	name: string;
	createdAt?: Date;
	updatedAt?: Date;
}

type SpeciesCreationAttributes = Pick<SpeciesAttributes, "name">;

export class Species extends Model<SpeciesAttributes, SpeciesCreationAttributes> {
	get id(): number {
		return this.getDataValue("id");
	}
	get name(): string {
		return this.getDataValue("name");
	}
	get createdAt(): Date | undefined {
		return this.getDataValue("createdAt");
	}
	get updatedAt(): Date | undefined {
		return this.getDataValue("updatedAt");
	}
}

Species.init(
	{
		id: {
			type: DataTypes.INTEGER.UNSIGNED,
			autoIncrement: true,
			primaryKey: true,
			field: "id",
		},
		name: {
			type: DataTypes.STRING,
			allowNull: false,
			unique: true,
			field: "name",
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
		tableName: "species",
		modelName: "Species",
		timestamps: true,
	}
);
