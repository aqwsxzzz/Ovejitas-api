import { DataTypes, Model, Association } from "sequelize";
import { Sequelize } from "sequelize";
// eslint-disable-next-line @typescript-eslint/no-var-requires
const sequelizeConfig = require("../config/sequelize-config")[process.env.NODE_ENV || "development"];
import { SpeciesTranslation } from "./species-translation-model";

const sequelize = new Sequelize(sequelizeConfig);

export interface SpeciesAttributes {
	id: number;
	createdAt?: Date;
	updatedAt?: Date;
}

type SpeciesCreationAttributes = {};

export class Species extends Model<SpeciesAttributes, SpeciesCreationAttributes> {
	get id(): number {
		return this.getDataValue("id");
	}
	get createdAt(): Date | undefined {
		return this.getDataValue("createdAt");
	}
	get updatedAt(): Date | undefined {
		return this.getDataValue("updatedAt");
	}
	public static associations: {
		translations: Association<Species, SpeciesTranslation>;
	};
}

Species.init(
	{
		id: {
			type: DataTypes.INTEGER.UNSIGNED,
			autoIncrement: true,
			primaryKey: true,
			field: "id",
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
