# File Patterns

## 1. Schema File (`{resource}.schema.ts`)

```typescript
import { Static, Type } from '@sinclair/typebox';
import { createGetEndpointSchema, createPostEndpointSchema } from '../../utils/schema-builder';

// Enums first
export enum ResourceStatus {
  Active = 'active',
  Inactive = 'inactive',
}

// Base schema
const ResourceSchema = Type.Object({
  id: Type.Integer({ minimum: 1 }),
  name: Type.String(),
  status: Type.Enum(ResourceStatus),
  createdAt: Type.String(),
  updatedAt: Type.String(),
}, { $id: 'resource', additionalProperties: false });

// Create/Update schemas
export const ResourceCreateSchema = Type.Object({
  name: Type.String(),
  status: Type.Optional(Type.Enum(ResourceStatus)),
}, { $id: 'resourceCreate', additionalProperties: false });

// Response schema (encoded IDs)
export const ResourceResponseSchema = Type.Object({
  ...ResourceSchema.properties,
  id: Type.String(), // Always string for encoded IDs
}, { $id: 'resourceResponse', additionalProperties: false });

// Generate static types
export type Resource = Static<typeof ResourceSchema>;
export type ResourceCreate = Static<typeof ResourceCreateSchema>;
export type ResourceResponse = Static<typeof ResourceResponseSchema>;

// Endpoint schemas
export const createResourceSchema = createPostEndpointSchema({
  body: ResourceCreateSchema,
  dataSchema: ResourceResponseSchema,
  errorCodes: [400],
});
```

## 2. Model File (`{resource}.model.ts`)

```typescript
import { DataTypes, Model, Sequelize } from 'sequelize';
import { Resource, ResourceStatus } from './resource.schema';

type ResourceCreationAttributes = Pick<Resource, 'name'> & Partial<Pick<Resource, 'status'>>;

export class ResourceModel extends Model<Resource, ResourceCreationAttributes> {
  declare id: number;
  declare name: string;
  declare status: string;
  declare createdAt: string;
  declare updatedAt: string;
}

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
});
```

## 3. Service File (`{resource}.service.ts`)

```typescript
import { BaseService } from '../../services/base.service';
import { ResourceModel } from './resource.model';
import { ResourceCreate } from './resource.schema';
import { decodeId } from '../../utils/id-hash-util';
import { FindOptions } from 'sequelize';

export class ResourceService extends BaseService {
  
  async getResources(farmId: number): Promise<ResourceModel[]> {
    const findOptions: FindOptions = {
      where: { farmId },
    };
    
    return this.db.sequelize.models.Resource.findAll(findOptions) as ResourceModel[];
  }

  async createResource(data: ResourceCreate & { farmId: number }): Promise<ResourceModel> {
    return this.db.sequelize.transaction(async (transaction) => {
      // Process/decode any IDs
      const processedData = { ...data };
      
      // Add validation logic here
      
      return this.db.sequelize.models.Resource.create(processedData, { transaction }) as ResourceModel;
    });
  }
}
```

## 4. Routes File (`{resource}.routes.ts`)

```typescript
import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { ResourceCreate, createResourceSchema, listResourceSchema } from './resource.schema';
import { ResourceSerializer } from './resource.serializer';

const resourceRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {
  
  fastify.get('/', {
    schema: listResourceSchema,
    preHandler: fastify.authenticate,
  }, async (request, reply) => {
    try {
      const farmId = request.lastVisitedFarmId;
      const resources = await fastify.resourceService.getResources(farmId);
      const serialized = ResourceSerializer.serializeMany(resources);
      reply.success(serialized);
    } catch (error) {
      fastify.handleDbError(error, reply);
    }
  });

  fastify.post('/', {
    schema: createResourceSchema,
    preHandler: fastify.authenticate,
  }, async (request: FastifyRequest<{ Body: ResourceCreate }>, reply) => {
    try {
      const farmId = request.lastVisitedFarmId;
      const resource = await fastify.resourceService.createResource({
        ...request.body,
        farmId,
      });
      const serialized = ResourceSerializer.serialize(resource);
      reply.success(serialized);
    } catch (error) {
      fastify.handleDbError(error, reply);
    }
  });
};

export default resourceRoutes;
```

## 5. Serializer File (`{resource}.serializer.ts`)

```typescript
import { encodeId } from '../../utils/id-hash-util';
import { ResourceResponse } from './resource.schema';
import { ResourceModel } from './resource.model';

export class ResourceSerializer {
  static serialize(resource: ResourceModel): ResourceResponse {
    return {
      id: encodeId(resource.id),
      name: resource.name,
      status: resource.status as ResourceResponse['status'],
      createdAt: resource.createdAt,
      updatedAt: resource.updatedAt,
    };
  }

  static serializeMany(resources: ResourceModel[]): ResourceResponse[] {
    return resources.map(resource => this.serialize(resource));
  }
}
```

## 6. Index File (`index.ts`)

```typescript
import { FastifyPluginAsync } from 'fastify';
import resourceRoutes from './resource.routes';

const resourcePlugin: FastifyPluginAsync = async (fastify) => {
  await fastify.register(resourceRoutes, { prefix: '/resources' });
};

export default resourcePlugin;
```
