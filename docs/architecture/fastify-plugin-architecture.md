# Fastify Plugin Architecture

## Overview

This document describes the Fastify plugin-based architecture implemented in the Ovejitas-api project. The architecture leverages Fastify's powerful plugin system to create a modular, scalable, and maintainable codebase.

## Architecture Principles

### 1. Plugin Separation
- **Core Plugins**: Use `fastify-plugin` for application-wide functionality
- **Resource Plugins**: Standard async functions for business domain resources
- **Service Decorators**: All services registered as Fastify decorators for reusability

### 2. Autoloading Strategy
- Resources are automatically loaded from the `/src/resources` directory
- Each resource must have an `index.ts` file as the entry point
- Routes are registered with appropriate prefixes at the plugin level

## Project Structure

```
src/
├── server.ts                    # Main application entry point
├── plugins/                     # Core plugins (manually registered)
│   ├── database.plugin.ts       # Database connection (fastify-plugin)
│   ├── services.plugin.ts       # Service decorator registration (fastify-plugin)
│   ├── authentication.plugin.ts # JWT authentication (fastify-plugin)
│   ├── error-handler.ts         # Global error handling (fastify-plugin)
│   └── custom-reply.plugin.ts   # Response helpers (fastify-plugin)
├── resources/                   # Business domain resources (autoloaded)
│   ├── animal/
│   │   ├── index.ts            # Plugin entry point
│   │   ├── animal.routes.ts    # Route definitions
│   │   ├── animal.model.ts     # Sequelize model
│   │   ├── animal.schema.ts    # Validation schemas
│   │   ├── animal.service.ts   # Business logic
│   │   └── animal.serializer.ts # Response transformation
│   └── [other resources follow same pattern]
├── services/
│   └── base.service.ts         # Base service class
├── utils/                      # Utility functions
└── types/                      # TypeScript declarations
    └── fastify.d.ts           # Extended Fastify interfaces
```

## Core Plugins

### Database Plugin (`database.plugin.ts`)
```typescript
export default fastifyPlugin(databasePlugin, {
	name: 'database-plugin',
});
```
- Initializes Sequelize connection
- Decorates Fastify instance with `db` property
- Handles connection lifecycle

### Services Plugin (`services.plugin.ts`)
```typescript
export default fastifyPlugin(servicesPlugin, {
	name: 'services-plugin',
	dependencies: ['database-plugin'],
});
```
- Registers all services as Fastify decorators
- Ensures services are available across all plugins
- Depends on database plugin for initialization

### Authentication Plugin (`authentication.plugin.ts`)
```typescript
export default fp(async function authenticationPlugin(fastify) {
	fastify.decorate('authenticate', async function (request, reply) {
		// JWT authentication logic
	});
});
```
- Provides authentication decorator
- Handles JWT token validation
- Sets user context on requests

## Resource Plugin Pattern

Each resource follows a consistent pattern:

### 1. Index File (`index.ts`)
```typescript
import { FastifyPluginAsync } from 'fastify';
import animalRoutes from './animal.routes';

const animalPlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(animalRoutes, { prefix: '/animals' });
};

export default animalPlugin;
```

### 2. Routes File (`[resource].routes.ts`)
```typescript
const animalRoutes: FastifyPluginAsync = async (fastify) => {
	// Use decorated service instead of creating new instance
	fastify.get('/', async (request, reply) => {
		try {
			const animals = await fastify.animalService.getAnimals();
			reply.success(animals);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default animalRoutes;
```

## Server Configuration

### Autoloading Implementation
```typescript
// server.ts
import fastifyAutoload from '@fastify/autoload';

// Register core plugins manually
server.register(databasePlugin);
server.register(servicesPlugin);
server.register(authenticationPlugin);

// Auto-load all resource plugins
server.register(fastifyAutoload, {
	dir: path.join(__dirname, 'resources'),
	options: { prefix: '/api/v1' },
	matchFilter: (path) => path.endsWith('index.ts') || path.endsWith('index.js'),
});
```

## Service Registration

### TypeScript Declarations
```typescript
// types/fastify.d.ts
declare module 'fastify' {
	interface FastifyInstance {
		// Services
		animalService: AnimalService;
		farmService: FarmService;
		// ... other services
	}
}
```

### Service Decorator Pattern
```typescript
// plugins/services.plugin.ts
fastify.decorate('animalService', new AnimalService(fastify.db));
fastify.decorate('farmService', new FarmService(fastify.db));
// ... other services
```

## Benefits

### 1. **Modularity**
- Each resource is self-contained
- Easy to add/remove features
- Clear separation of concerns

### 2. **Reusability**
- Services available across all plugins
- Shared utilities and helpers
- Consistent error handling

### 3. **Scalability**
- Automatic resource discovery
- Plugin-level route prefixing
- Easy to split into microservices

### 4. **Maintainability**
- Consistent file structure
- Clear naming conventions
- Standardized patterns

### 5. **Testing**
- Services can be mocked via decorators
- Plugins can be tested in isolation
- Clear dependency injection

## Migration Guide

To add a new resource:

1. Create resource directory: `/src/resources/[resource-name]/`
2. Create `index.ts` with plugin registration
3. Create `[resource-name].routes.ts` with route definitions
4. Create supporting files (model, service, schema, serializer)
5. Add service to `services.plugin.ts`
6. Update TypeScript declarations in `fastify.d.ts`

## Best Practices

### 1. **Plugin Dependencies**
- Core plugins should declare dependencies explicitly
- Resource plugins should not depend on each other directly
- Use service decorators for cross-resource communication

### 2. **Error Handling**
- Always use try-catch blocks in routes
- Use `fastify.handleDbError` for database errors
- Provide meaningful error messages

### 3. **Route Organization**
- Group related routes in the same file
- Use consistent naming for route handlers
- Apply appropriate authentication/authorization

### 4. **Service Pattern**
- Extend BaseService for common functionality
- Keep business logic in services, not routes
- Use serializers for response transformation

### 5. **Validation**
- Define schemas using TypeBox or JSON Schema
- Validate at route level using Fastify schemas
- Keep validation separate from business logic

## Performance Considerations

### 1. **Plugin Loading Order**
1. Database connection
2. Service registration
3. Authentication
4. Resource autoloading

### 2. **Encapsulation**
- Resource plugins create separate contexts
- Core plugins use `fastify-plugin` to break encapsulation
- Services are shared across all contexts

### 3. **Route Registration**
- Routes are registered once at startup
- Prefixes are applied at plugin level
- No runtime route resolution overhead

## Security Considerations

### 1. **Authentication**
- Applied at route level using preHandler
- JWT tokens validated on each request
- User context available in request object

### 2. **Multi-tenancy**
- Farm-based isolation enforced in services
- User permissions checked in routes
- Data access controlled by business logic

### 3. **Input Validation**
- Schemas validate all input data
- Additional properties rejected by default
- Type coercion handled by Fastify

## Conclusion

This plugin-based architecture provides a robust foundation for building scalable Fastify applications. By leveraging Fastify's plugin system, autoloading capabilities, and decorator pattern, we achieve a clean, maintainable, and performant codebase that can grow with the application's needs.