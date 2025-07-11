# Temporal Feature Coding Standards

## Overview
This document defines the coding standards for implementing the temporal tracking features in the Ovejitas-api project. All code must follow these standards to maintain consistency with the existing codebase.

## File Naming Conventions

### Models
- **Pattern**: `{entity}-model.ts`
- **Location**: `/src/models/`
- **Examples**: 
  - `animal-measurement-model.ts`
  - `animal-health-record-model.ts`
  - `animal-location-model.ts`

### Types
- **Pattern**: `{entity}-types.ts`
- **Location**: `/src/types/`
- **Examples**:
  - `animal-measurement-types.ts`
  - `animal-health-record-types.ts`
  - `animal-location-types.ts`

### Controllers
- **Pattern**: `{entity}-controller.ts`
- **Location**: `/src/controllers/v1/`
- **Examples**:
  - `animal-measurement-controller.ts`
  - `animal-health-controller.ts`

### Routes
- **Pattern**: `{entity}-route.ts` or `{entity}-routes.ts`
- **Location**: `/src/routes/v1/`
- **Examples**:
  - `animal-measurement-routes.ts`
  - `animal-health-routes.ts`

### Schemas
- **Pattern**: `{entity}-schema.ts`
- **Location**: `/src/schemas/`
- **Examples**:
  - `animal-measurement-schema.ts`
  - `animal-health-record-schema.ts`

### Serializers
- **Pattern**: `{entity}-serializer.ts`
- **Location**: `/src/serializers/`
- **Examples**:
  - `animal-measurement-serializer.ts`
  - `animal-health-serializer.ts`

### Migrations
- **Pattern**: `{timestamp}-{description}-migration.js`
- **Location**: `/src/migrations/`
- **Examples**:
  - `20250111000000-create-animal-measurements-table-migration.js`
  - `20250111000001-create-animal-health-records-table-migration.js`

## Type Definitions

### Structure for Each Entity Type File

```typescript
// animal-measurement-types.ts

// Model attributes interface
export interface AnimalMeasurementAttributes {
  id: number;
  animalId: number;
  measurementType: 'weight' | 'height' | 'body_condition';
  value: number;
  unit: string;
  measuredAt: Date;
  measuredBy?: number | null;
  method?: string | null;
  notes?: string | null;
  createdAt: Date;
  updatedAt: Date;
}

// Creation attributes type (omit auto-generated fields)
export type AnimalMeasurementCreationAttributes = Omit<
  AnimalMeasurementAttributes, 
  'id' | 'createdAt' | 'updatedAt'
> & {
  measuredAt?: Date; // Optional if has default
};

// Request body interfaces
export interface IAnimalMeasurementCreateBody {
  measurementType: 'weight' | 'height' | 'body_condition';
  value: number;
  unit: string;
  measuredAt?: string; // ISO date string
  method?: string;
  notes?: string;
}

export interface IAnimalMeasurementUpdateBody {
  value?: number;
  unit?: string;
  measuredAt?: string;
  method?: string;
  notes?: string;
}

// Request params
export interface IAnimalMeasurementParams {
  farmId: string;
  animalId: string;
  measurementId: string;
}

// Route interfaces
export interface AnimalMeasurementCreateRoute extends RouteGenericInterface {
  Body: IAnimalMeasurementCreateBody;
  Params: Pick<IAnimalMeasurementParams, 'farmId' | 'animalId'>;
}

export interface AnimalMeasurementListRoute extends RouteGenericInterface {
  Params: Pick<IAnimalMeasurementParams, 'farmId' | 'animalId'>;
  Querystring: {
    measurementType?: 'weight' | 'height' | 'body_condition';
    startDate?: string;
    endDate?: string;
    limit?: number;
  };
}
```

## Model Implementation Standards

### Model Association Rules

**IMPORTANT**: Model associations must NEVER be defined within the model files. All associations are centralized in `/src/models/associations.ts`.

```typescript
// associations.ts - Add new associations here
import { AnimalMeasurement } from "./animal-measurement-model";
import { Animal } from "./animal-model";
import { User } from "./user-model";

// Temporal model associations
AnimalMeasurement.belongsTo(Animal, { foreignKey: "animalId", as: "animal" });
AnimalMeasurement.belongsTo(User, { foreignKey: "measuredBy", as: "measurer" });
Animal.hasMany(AnimalMeasurement, { foreignKey: "animalId", as: "measurements" });
```

### Model Definition Structure

```typescript
// animal-measurement-model.ts
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
  // Getter for each property
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
      field: "animal_id", // snake_case in DB
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
```

## Controller Implementation Standards

```typescript
// animal-measurement-controller.ts
import { FastifyReply, FastifyRequest } from "fastify";
import { AnimalMeasurement } from "../../models/animal-measurement-model";
import { Animal } from "../../models/animal-model";
import { serializeAnimalMeasurement } from "../../serializers/animal-measurement-serializer";
import { 
  AnimalMeasurementCreateRoute,
  AnimalMeasurementListRoute 
} from "../../types/animal-measurement-types";

export async function createAnimalMeasurement(
  request: FastifyRequest<AnimalMeasurementCreateRoute>,
  reply: FastifyReply
): Promise<FastifyReply> {
  const { farmId, animalId } = request.params;
  const { measurementType, value, unit, measuredAt, method, notes } = request.body;
  
  // Decode IDs
  const decodedFarmId = request.server.decodeId(farmId);
  const decodedAnimalId = request.server.decodeId(animalId);
  
  // Verify animal belongs to farm
  const animal = await Animal.findOne({
    where: {
      id: decodedAnimalId,
      farmId: decodedFarmId,
    },
  });
  
  if (!animal) {
    return reply.status(404).send({
      error: "Animal not found",
    });
  }
  
  // Create measurement
  const measurement = await AnimalMeasurement.create({
    animalId: decodedAnimalId,
    measurementType,
    value,
    unit,
    measuredAt: measuredAt ? new Date(measuredAt) : new Date(),
    measuredBy: request.userId,
    method,
    notes,
  });
  
  return reply.status(201).send({
    data: serializeAnimalMeasurement(measurement, request.server),
  });
}

export async function listAnimalMeasurements(
  request: FastifyRequest<AnimalMeasurementListRoute>,
  reply: FastifyReply
): Promise<FastifyReply> {
  const { farmId, animalId } = request.params;
  const { measurementType, startDate, endDate, limit = 100 } = request.query;
  
  const decodedFarmId = request.server.decodeId(farmId);
  const decodedAnimalId = request.server.decodeId(animalId);
  
  // Build where clause
  const where: any = { animalId: decodedAnimalId };
  
  if (measurementType) {
    where.measurementType = measurementType;
  }
  
  if (startDate || endDate) {
    where.measuredAt = {};
    if (startDate) where.measuredAt[Op.gte] = new Date(startDate);
    if (endDate) where.measuredAt[Op.lte] = new Date(endDate);
  }
  
  const measurements = await AnimalMeasurement.findAll({
    where,
    order: [["measuredAt", "DESC"]],
    limit: Math.min(limit, 1000),
  });
  
  return reply.send({
    data: measurements.map(m => serializeAnimalMeasurement(m, request.server)),
  });
}
```

## Import Order Convention

1. External libraries
2. Models
3. Serializers
4. Utils
5. Types

```typescript
// Correct import order
import { FastifyReply, FastifyRequest } from "fastify";
import { Op } from "sequelize";
import { AnimalMeasurement } from "../../models/animal-measurement-model";
import { Animal } from "../../models/animal-model";
import { serializeAnimalMeasurement } from "../../serializers/animal-measurement-serializer";
import { validateDateRange } from "../../utils/date-util";
import { AnimalMeasurementCreateRoute } from "../../types/animal-measurement-types";
```

## Virtual Fields for Enhanced Animal Model

```typescript
// In animal-model.ts, add virtual fields using Sequelize VIRTUAL type
{
  currentWeight: {
    type: DataTypes.VIRTUAL,
    async get() {
      const measurement = await AnimalMeasurement.findOne({
        where: { 
          animalId: this.id,
          measurementType: 'weight'
        },
        order: [['measuredAt', 'DESC']],
      });
      return measurement?.value || null;
    },
  },
  currentLocation: {
    type: DataTypes.VIRTUAL,
    async get() {
      const location = await AnimalLocation.findOne({
        where: { animalId: this.id },
        order: [['movedAt', 'DESC']],
      });
      return location?.locationName || null;
    },
  },
}
```

## API Route Patterns

```typescript
// animal-measurement-routes.ts
export default async function animalMeasurementRoutes(
  fastify: FastifyInstance
): Promise<void> {
  // List measurements for an animal
  fastify.get(
    "/farms/:farmId/animals/:animalId/measurements",
    {
      preValidation: [fastify.authenticate],
      schema: listAnimalMeasurementsSchema,
    },
    listAnimalMeasurements
  );
  
  // Create new measurement
  fastify.post(
    "/farms/:farmId/animals/:animalId/measurements",
    {
      preValidation: [fastify.authenticate],
      schema: createAnimalMeasurementSchema,
    },
    createAnimalMeasurement
  );
  
  // Get specific measurement
  fastify.get(
    "/farms/:farmId/animals/:animalId/measurements/:measurementId",
    {
      preValidation: [fastify.authenticate],
      schema: getAnimalMeasurementSchema,
    },
    getAnimalMeasurement
  );
}
```

## Database Naming Conventions

- **Tables**: snake_case plural (e.g., `animal_measurements`)
- **Columns**: snake_case (e.g., `measured_at`, `measurement_type`)
- **Indexes**: `idx_{table}_{columns}` (e.g., `idx_animal_measurements_animal_type_time`)
- **Foreign keys**: `{related_table}_id` (e.g., `animal_id`, `measured_by`)

## Type Safety Rules

1. **Never use `any` type** - Always define proper types
2. **Use union types** for enums: `'weight' | 'height' | 'body_condition'`
3. **Use optional chaining** for nullable fields: `measurement?.value`
4. **Define all request/response types** in the types file
5. **Use `null | undefined` for optional fields** in model getters

## Error Handling Pattern

```typescript
if (!animal) {
  return reply.status(404).send({
    error: "Animal not found",
  });
}

try {
  // Operation
} catch (error) {
  return reply.status(500).send({
    error: "Internal server error",
  });
}
```

## Testing Conventions

- Test files: `{entity}.test.ts`
- Location: `/src/tests/`
- Use descriptive test names
- Test both success and error cases

These standards ensure consistency with the existing codebase while implementing the new temporal tracking features.