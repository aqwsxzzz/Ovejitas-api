import { DataTypes, Model } from "sequelize";
import { Sequelize } from "sequelize";
// eslint-disable-next-line @typescript-eslint/no-var-requires
const sequelizeConfig = require("../config/sequelize-config")[process.env.NODE_ENV || "development"];

const sequelize = new Sequelize(sequelizeConfig);
import { Species } from "./species-model";

export interface SpeciesTranslationAttributes {
	id: number;
	speciesId: number;
	languageCode: string;
	name: string;
	createdAt?: Date;
	updatedAt?: Date;
}

type SpeciesTranslationCreationAttributes = Omit<SpeciesTranslationAttributes, "id" | "createdAt" | "updatedAt">;

export class SpeciesTranslation extends Model<SpeciesTranslationAttributes, SpeciesTranslationCreationAttributes> {
	get id(): number {
		return this.getDataValue("id");
	}
	get speciesId(): number {
		return this.getDataValue("speciesId");
	}
	get languageCode(): string {
		return this.getDataValue("languageCode");
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

SpeciesTranslation.init(
	{
		id: {
			type: DataTypes.INTEGER.UNSIGNED,
			autoIncrement: true,
			primaryKey: true,
			field: "id",
		},
		speciesId: {
			type: DataTypes.INTEGER.UNSIGNED,
			allowNull: false,
			field: "species_id",
			references: {
				model: "species",
				key: "id",
			},
			onDelete: "CASCADE",
		},
		languageCode: {
			type: DataTypes.STRING(5),
			allowNull: false,
			field: "language_code",
		},
		name: {
			type: DataTypes.STRING,
			allowNull: false,
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
		tableName: "species_translation",
		modelName: "SpeciesTranslation",
		timestamps: true,
		indexes: [
			{
				unique: true,
				fields: ["speciesId", "name"],
			},
			{
				unique: true,
				fields: ["name", "languageCode"],
			},
		],
	}
);

Species.hasMany(SpeciesTranslation, { foreignKey: "speciesId", as: "translations" });
SpeciesTranslation.belongsTo(Species, { foreignKey: "speciesId", as: "species" });
