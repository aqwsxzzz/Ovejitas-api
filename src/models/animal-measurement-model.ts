import { DataTypes, Model } from "sequelize";
import { Sequelize } from "sequelize";
import { 
  AnimalMeasurementAttributes, 
  AnimalMeasurementCreationAttributes 
} from "../types/animal-measurement-types";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const sequelizeConfig = require("../config/sequelize-config")[process.env.NODE_ENV || "development"];
const sequelize = new Sequelize(sequelizeConfig);

export class AnimalMeasurement extends Model<
  AnimalMeasurementAttributes, 
  AnimalMeasurementCreationAttributes
> {
  get id(): number {
    return this.getDataValue("id");
  }
  
  get animalId(): number {
    return this.getDataValue("animalId");
  }
  
  get measurementType(): string {
    return this.getDataValue("measurementType");
  }
  
  get value(): number {
    return this.getDataValue("value");
  }
  
  get unit(): string {
    return this.getDataValue("unit");
  }
  
  get measuredAt(): Date {
    return this.getDataValue("measuredAt");
  }
  
  get measuredBy(): number | null | undefined {
    return this.getDataValue("measuredBy");
  }
  
  get method(): string | null | undefined {
    return this.getDataValue("method");
  }
  
  get notes(): string | null | undefined {
    return this.getDataValue("notes");
  }
  
  get createdAt(): Date {
    return this.getDataValue("createdAt");
  }
  
  get updatedAt(): Date {
    return this.getDataValue("updatedAt");
  }
}

AnimalMeasurement.init(
  {
    id: {
      type: DataTypes.BIGINT,
      primaryKey: true,
      autoIncrement: true,
    },
    animalId: {
      type: DataTypes.BIGINT,
      allowNull: false,
      field: "animal_id",
      references: {
        model: "animals",
        key: "id",
      },
    },
    measurementType: {
      type: DataTypes.ENUM("weight", "height", "body_condition"),
      allowNull: false,
      field: "measurement_type",
    },
    value: {
      type: DataTypes.DECIMAL(10, 2),
      allowNull: false,
      validate: {
        min: 0,
      },
    },
    unit: {
      type: DataTypes.STRING(10),
      allowNull: false,
    },
    measuredAt: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
      field: "measured_at",
    },
    measuredBy: {
      type: DataTypes.BIGINT,
      allowNull: true,
      field: "measured_by",
      references: {
        model: "users",
        key: "id",
      },
    },
    method: {
      type: DataTypes.STRING(50),
      allowNull: true,
    },
    notes: {
      type: DataTypes.TEXT,
      allowNull: true,
    },
    createdAt: {
      type: DataTypes.DATE,
      allowNull: false,
      field: "created_at",
    },
    updatedAt: {
      type: DataTypes.DATE,
      allowNull: false,
      field: "updated_at",
    },
  },
  {
    sequelize,
    tableName: "animal_measurements",
    modelName: "AnimalMeasurement",
    timestamps: true,
    indexes: [
      {
        name: "idx_animal_measurements_animal_type_time",
        fields: ["animal_id", "measurement_type", "measured_at"],
      },
      {
        name: "idx_animal_measurements_time",
        fields: ["measured_at"],
      },
    ],
  }
);