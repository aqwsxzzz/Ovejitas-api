# Ovejitas-api Coding Standards v2

## Overview
This document defines the coding standards for the Ovejitas-api project based on the actual Fastify plugin-based architecture implementation. All code must follow these standards to maintain consistency with the existing codebase patterns.

## Architecture Principles

### 1. Plugin-Based Structure
- **Core Plugins**: Use `fastify-plugin` for application-wide functionality
- **Resource Plugins**: Standard async functions for business domain resources  
- **Service Decorators**: All services registered as Fastify decorators for reusability
- **Autoloading**: Resources automatically loaded from `/src/resources` directory

### 2. Resource-Centric Organization
Each business domain is organized as a complete resource with:
- `index.ts` - Plugin entry point
- `{resource}.routes.ts` - Route definitions
- `{resource}.model.ts` - Sequelize model
- `{resource}.schema.ts` - TypeBox schemas and type definitions
- `{resource}.service.ts` - Business logic extending BaseService
- `{resource}.serializer.ts` - Response transformation

## File Structure & Naming Conventions

### Resource Directory Structure
```
src/resources/{resource-name}/
├── index.ts                    # Plugin entry point
├── {resource-name}.routes.ts   # Route definitions
├── {resource-name}.model.ts    # Sequelize model
├── {resource-name}.schema.ts   # TypeBox schemas + Static types
├── {resource-name}.service.ts  # Business logic service
└── {resource-name}.serializer.ts # Response transformation
```

### Naming Patterns
- **Resources**: `kebab-case` directory names (e.g., `animal-measurement`)
- **Files**: `{resource-name}.{type}.ts` format
- **Models**: `{ResourceName}Model` class names (e.g., `AnimalModel`)
- **Services**: `{ResourceName}Service` class names (e.g., `AnimalService`)
- **Serializers**: `{ResourceName}Serializer` class names (e.g., `AnimalSerializer`)

### Database Conventions
- **Tables**: `snake_case` plural (e.g., `animal_measurements`)
- **Columns**: `snake_case` with `field` mapping (e.g., `farmId` → `farm_id`)
- **Indexes**: `idx_{table}_{columns}` or unique constraints
- **Foreign keys**: `{related_table_singular}_id` (e.g., `animal_id`, `farm_id`)

## Schema & Type Definition Standards

### Schema Structure (TypeBox + Static Types)
```typescript
import { Type, Static } from '@sinclair/typebox';
import { createPostEndpointSchema, createGetEndpointSchema } from '../../utils/schema-builder';

// Enum definitions
export enum ResourceStatus {
  Active = 'active',
  Inactive = 'inactive',
}

// Base schema definition
const ResourceSchema = Type.Object({
  id: Type.Integer({ minimum: 1 }),
  name: Type.String(),
  status: Type.Enum(ResourceStatus),
  createdAt: Type.String(),
  updatedAt: Type.String(),
}, {
  $id: 'resource',
  additionalProperties: false,
});

// Create/Update schemas
export const ResourceCreateSchema = Type.Object({
  name: Type.String(),
  status: Type.Optional(Type.Enum(ResourceStatus)),
}, {
  $id: 'resourceCreate',
  additionalProperties: false,
});

// Response schema with encoded IDs
export const ResourceResponseSchema = Type.Object({
  ...ResourceSchema.properties,
  id: Type.String(), // Encoded ID
}, {
  $id: 'resourceResponse',
  additionalProperties: false,
});

// Static type generation
export type Resource = Static<typeof ResourceSchema>;
export type ResourceCreate = Static<typeof ResourceCreateSchema>;
export type ResourceResponse = Static<typeof ResourceResponseSchema>;

// Endpoint schemas using schema-builder
export const createResourceSchema = createPostEndpointSchema({
  body: ResourceCreateSchema,
  dataSchema: ResourceResponseSchema,
  errorCodes: [400, 409],
});

export const listResourceSchema = createGetEndpointSchema({
  dataSchema: Type.Array(ResourceResponseSchema),
  errorCodes: [404],
});
```

### Include/Relationship Type Patterns
```typescript
// Model with possible includes (from database)
export type ResourceWithPossibleIncludes = ResourceModel & {
  relatedEntity?: RelatedEntityModel;
  nestedRelation?: NestedRelationModel[];
};

// Response with includes (serialized)
export type ResourceWithIncludes = ResourceResponse & {
  relatedEntity?: RelatedEntityResponse;
  nestedRelation?: NestedRelationResponse[];
};
```

## Model Implementation Standards

### Model Structure (No Getters)
```typescript
import { DataTypes, Model, Sequelize } from 'sequelize';
import { Resource, ResourceStatus } from './resource.schema';

// Creation attributes type
type ResourceCreationAttributes = Pick<Resource, 'name'> & 
  Partial<Pick<Resource, 'status'>>;

export class ResourceModel extends Model<Resource, ResourceCreationAttributes> {
  // Declare properties for TypeScript (no getters!)
  declare id: number;
  declare name: string;
  declare status: string;
  declare createdAt: string;
  declare updatedAt: string;
}

// Init function pattern
export const initResourceModel = (sequelize: Sequelize) => ResourceModel.init({
  id: {
    type: DataTypes.INTEGER.UNSIGNED,
    autoIncrement: true,
    primaryKey: true,
    field: 'id',
  },
  name: {
    type: DataTypes.STRING,
    allowNull: false,
    field: 'name',
  },
  status: {
    type: DataTypes.ENUM(...Object.values(ResourceStatus)),
    allowNull: false,
    field: 'status',
    defaultValue: ResourceStatus.Active,
  },
  createdAt: {
    type: DataTypes.DATE,
    allowNull: false,
    defaultValue: DataTypes.NOW,
    field: 'created_at',
  },
  updatedAt: {
    type: DataTypes.DATE,
    allowNull: false,
    defaultValue: DataTypes.NOW,
    field: 'updated_at',
  },
}, {
  sequelize,
  tableName: 'resources',
  modelName: 'Resource',
  timestamps: true,
  indexes: [
    // Define indexes here
  ],
});
```

## Service Implementation Standards

### Service Structure (Extending BaseService)
```typescript
import { BaseService } from '../../services/base.service';
import { ResourceModel } from './resource.model';
import { ResourceCreate } from './resource.schema';
import { decodeId } from '../../utils/id-hash-util';
import { IncludeParser, TypedIncludeConfig } from '../../utils/include-parser';
import { FindOptions, Transaction } from 'sequelize';

export class ResourceService extends BaseService {
  
  // Define allowed includes with strict typing
  private static readonly ALLOWED_INCLUDES = IncludeParser.createConfig({
    relatedEntity: {
      model: 'RelatedEntity' as const,
      as: 'relatedEntity',
      attributes: ['id', 'name', 'createdAt', 'updatedAt'],
    },
  } satisfies TypedIncludeConfig);

  async getResources(farmId: number, includeParam?: string): Promise<ResourceModel[] | null> {
    const findOptions: FindOptions = {
      where: { farmId },
    };

    if (includeParam) {
      this.validateIncludes(includeParam, ResourceService.ALLOWED_INCLUDES);
      findOptions.include = this.parseIncludes(includeParam, ResourceService.ALLOWED_INCLUDES);
    }

    return this.db.models.Resource.findAll(findOptions);
  }

  async createResource({ data }: { data: ResourceCreate & { farmId: number } }): Promise<ResourceModel | null> {
    return this.db.sequelize.transaction(async (transaction) => {
      // Decode any encoded IDs
      const processedData = {
        ...data,
        // Add any ID decoding logic here
      };

      // Validation logic
      await this.validateSomething(processedData, transaction);

      return this.db.models.Resource.create(processedData, { transaction });
    });
  }

  // Private validation methods
  private async validateSomething(data: any, transaction?: Transaction): Promise<void> {
    // Business logic validation
    if (!data.name) {
      throw new Error('Name is required');
    }
  }
}
```

## Route Implementation Standards

### Route Structure with Typed Requests
```typescript
import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { ResourceCreate, ResourceInclude, createResourceSchema, listResourceSchema } from './resource.schema';
import { ResourceSerializer } from './resource.serializer';

const resourceRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {
  
  // GET endpoint with typed request
  fastify.get('/', { 
    schema: listResourceSchema, 
    preHandler: fastify.authenticate 
  }, async (request: FastifyRequest<{Querystring: ResourceInclude}>, reply) => {
    try {
      const { include } = request.query;
      const farmId = request.lastVisitedFarmId;
      const resources = await fastify.resourceService.getResources(farmId, include);

      const serializedResources = ResourceSerializer.serializeMany(resources!);
      reply.success(serializedResources);
    } catch (error) {
      fastify.handleDbError(error, reply);
    }
  });

  // POST endpoint with typed request body
  fastify.post('/', { 
    schema: createResourceSchema, 
    preHandler: fastify.authenticate 
  }, async (request: FastifyRequest<{Body: ResourceCreate}>, reply) => {
    try {
      const farmId = request.lastVisitedFarmId;
      const resource = await fastify.resourceService.createResource({ 
        data: { ...request.body, farmId } 
      });
      const serializedResource = ResourceSerializer.serialize(resource!);
      reply.success(serializedResource);
    } catch (error) {
      fastify.handleDbError(error, reply);
    }
  });
};

export default resourceRoutes;
```

## Serializer Implementation Standards

### Serializer Structure
```typescript
import { encodeId } from '../../utils/id-hash-util';
import { ResourceResponse, ResourceWithIncludes, ResourceWithPossibleIncludes } from './resource.schema';

export class ResourceSerializer {
  static serialize(resource: ResourceWithPossibleIncludes): ResourceResponse {
    const base = {
      id: encodeId(resource.id),
      name: resource.name,
      status: resource.status as ResourceResponse['status'],
      createdAt: resource.createdAt,
      updatedAt: resource.updatedAt,
    };

    const result: ResourceWithIncludes = { ...base };

    // Handle optional includes
    if (resource.relatedEntity) {
      result.relatedEntity = {
        id: encodeId(resource.relatedEntity.id),
        name: resource.relatedEntity.name,
        createdAt: resource.relatedEntity.createdAt,
        updatedAt: resource.relatedEntity.updatedAt,
      };
    }

    return result;
  }

  static serializeMany(resources: ResourceWithPossibleIncludes[]): ResourceResponse[] {
    return resources.map(r => this.serialize(r));
  }
}
```

## Plugin Entry Point Standards

### Index File Structure
```typescript
import { FastifyPluginAsync } from 'fastify';
import resourceRoutes from './resource.routes';

const resourcePlugin: FastifyPluginAsync = async (fastify) => {
  await fastify.register(resourceRoutes, { prefix: '/resources' });
};

export default resourcePlugin;
```

## Schema Builder Usage

### Using Schema Builder Utilities
- Use `createPostEndpointSchema` for POST endpoints (returns 201)
- Use `createGetEndpointSchema` for GET endpoints (returns 200)
- Use `createUpdateEndpointSchema` for PUT/PATCH endpoints
- Use `createDeleteEndpointSchema` for DELETE endpoints

```typescript
export const updateResourceSchema = createUpdateEndpointSchema({
  body: ResourceUpdateSchema,
  params: Type.Object({ id: Type.String() }),
  dataSchema: ResourceResponseSchema,
  errorCodes: [400, 404],
});
```

## Import Order Convention

```typescript
// 1. External libraries
import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { Static, Type } from '@sinclair/typebox';

// 2. Schema builder utilities
import { createPostEndpointSchema, createGetEndpointSchema } from '../../utils/schema-builder';

// 3. Related resource schemas (if needed)
import { RelatedResourceResponse, RelatedResourceResponseSchema } from '../related-resource/related-resource.schema';

// 4. Models
import { ResourceModel } from './resource.model';

// 5. Utils
import { encodeId, decodeId } from '../../utils/id-hash-util';
```

## Error Handling Standards

### Route Error Handling
```typescript
try {
  const result = await fastify.resourceService.someOperation();
  reply.success(result);
} catch (error) {
  fastify.handleDbError(error, reply);
}
```

### Service Error Handling
```typescript
// Throw descriptive errors in services
if (!entity) {
  throw new Error('Entity not found');
}

if (violation) {
  throw new Error('Business rule violation: specific message');
}
```

## Code Quality Rules

1. **Use TypeBox schemas** for all validation and type generation
2. **Generate Static types** from schemas using `Static<typeof Schema>`
3. **No getter methods** in models - use `declare` for TypeScript awareness
4. **Extend BaseService** for all service classes
5. **Use schema-builder utilities** for consistent endpoint schemas
6. **Encode/decode IDs** using `id-hash-util` in serializers and services
7. **Type route requests** when accessing body, params, or querystring
8. **Use include parsers** for dynamic query includes with validation
9. **Handle transactions** in services for complex operations
10. **Serialize all responses** consistently using static serializer methods

## Development Workflow

### Adding New Resources
1. Create resource directory: `/src/resources/{resource-name}/`
2. Define schemas with TypeBox and generate Static types
3. Implement model with `declare` properties and init function
4. Create service extending BaseService with include configs
5. Implement routes with typed requests
6. Create serializer with ID encoding
7. Create simple plugin index file
8. Register service in `services.plugin.ts`
9. Create database migrations
10. Add tests

This standards document reflects the actual implementation patterns found in the codebase and ensures consistency across all new resource development.