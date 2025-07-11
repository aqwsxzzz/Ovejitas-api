import { DataTypes, Model } from "sequelize";
import { Sequelize } from "sequelize";
// eslint-disable-next-line @typescript-eslint/no-var-requires
const sequelizeConfig = require("../config/sequelize-config")[process.env.NODE_ENV || "development"];
import { AnimalAttributes, AnimalCreationAttributes } from "../types/animal-types";

const sequelize = new Sequelize(sequelizeConfig);

export class Animal extends Model<AnimalAttributes, AnimalCreationAttributes> {
	get id(): number {
		return this.getDataValue("id");
	}
	get farmId(): number {
		return this.getDataValue("farmId");
	}
	get speciesId(): number {
		return this.getDataValue("speciesId");
	}
	get breedId(): number {
		return this.getDataValue("breedId");
	}
	get name(): string {
		return this.getDataValue("name");
	}
	get tagNumber(): string {
		return this.getDataValue("tagNumber");
	}
	get sex(): string {
		return this.getDataValue("sex");
	}
	get birthDate(): Date {
		return this.getDataValue("birthDate");
	}
	get weight(): number | null | undefined {
		return this.getDataValue("weight");
	}
	get status(): string {
		return this.getDataValue("status");
	}
	get reproductiveStatus(): string {
		return this.getDataValue("reproductiveStatus");
	}

	get fatherId(): number | null | undefined {
		return this.getDataValue("fatherId");
	}
	get motherId(): number | null | undefined {
		return this.getDataValue("motherId");
	}
	get acquisitionType(): string {
		return this.getDataValue("acquisitionType");
	}
	get acquisitionDate(): Date {
		return this.getDataValue("acquisitionDate");
	}
	get createdAt(): Date | undefined {
		return this.getDataValue("createdAt");
	}
	get updatedAt(): Date | undefined {
		return this.getDataValue("updatedAt");
	}
}

Animal.init(
	{
		id: {
			type: DataTypes.INTEGER.UNSIGNED,
			autoIncrement: true,
			primaryKey: true,
			field: "id",
		},
		farmId: {
			type: DataTypes.INTEGER.UNSIGNED,
			allowNull: false,
			field: "farm_id",
			references: { model: "farms", key: "id" },
			onDelete: "CASCADE",
		},
		speciesId: {
			type: DataTypes.INTEGER.UNSIGNED,
			allowNull: false,
			field: "species_id",
			references: { model: "species", key: "id" },
			onDelete: "CASCADE",
		},
		breedId: {
			type: DataTypes.INTEGER.UNSIGNED,
			allowNull: false,
			field: "breed_id",
			references: { model: "breeds", key: "id" },
			onDelete: "CASCADE",
		},
		name: {
			type: DataTypes.STRING,
			allowNull: false,
			field: "name",
		},
		tagNumber: {
			type: DataTypes.STRING,
			allowNull: false,
			field: "tag_number",
		},
		sex: {
			type: DataTypes.ENUM("male", "female", "unknown"),
			allowNull: false,
			field: "sex",
		},
		birthDate: {
			type: DataTypes.DATE,
			allowNull: false,
			field: "birth_date",
		},
		weight: {
			type: DataTypes.FLOAT,
			allowNull: true,
			field: "weight",
		},
		status: {
			type: DataTypes.ENUM("alive", "sold", "deceased"),
			allowNull: false,
			field: "status",
		},
		reproductiveStatus: {
			type: DataTypes.ENUM("open", "pregnant", "lactating", "other"),
			allowNull: false,
			field: "reproductive_status",
		},

		fatherId: {
			type: DataTypes.INTEGER.UNSIGNED,
			allowNull: true,
			field: "father_id",
			references: { model: "animals", key: "id" },
			onDelete: "SET NULL",
		},
		motherId: {
			type: DataTypes.INTEGER.UNSIGNED,
			allowNull: true,
			field: "mother_id",
			references: { model: "animals", key: "id" },
			onDelete: "SET NULL",
		},
		acquisitionType: {
			type: DataTypes.ENUM("born", "purchased", "other"),
			allowNull: false,
			field: "acquisition_type",
		},
		acquisitionDate: {
			type: DataTypes.DATE,
			allowNull: false,
			field: "acquisition_date",
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
		tableName: "animals",
		modelName: "Animal",
		timestamps: true,
		indexes: [
			{
				unique: true,
				fields: ["farm_id", "species_id", "tag_number"],
				where: { tag_number: { $ne: null } },
			},
		],
	}
);
