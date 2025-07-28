# Ovejitas-api Source Tree v2

## Project Structure (Post-Refactor)

```
ovejitas-api/
├── src/                               # Source code
│   ├── server.ts                      # Main application entry point
│   ├── database/                      # Database configuration & plugins
│   │   ├── database.plugin.ts         # Database connection plugin
│   │   ├── sequelize-config.js        # Sequelize configuration
│   │   ├── sequelize-config.d.ts      # TypeScript declarations
│   │   └── index.ts                   # Database initialization & associations
│   ├── plugins/                       # Core Fastify plugins
│   │   ├── services.plugin.ts         # Service decorator registration
│   │   ├── authentication-plugin.ts   # JWT authentication
│   │   ├── custom-reply.plugin.ts     # Response helpers (success/error)
│   │   └── error-handler.ts           # Global error handling
│   ├── resources/                     # Business domain resources (autoloaded)
│   │   ├── animal/                    # Animal management
│   │   │   ├── index.ts              # Plugin entry point
│   │   │   ├── animal.routes.ts      # Route definitions
│   │   │   ├── animal.model.ts       # Sequelize model
│   │   │   ├── animal.schema.ts      # Validation schemas
│   │   │   ├── animal.service.ts     # Business logic
│   │   │   └── animal.serializer.ts  # Response transformation
│   │   ├── animal-measurement/        # Animal measurements (temporal data)
│   │   │   ├── index.ts
│   │   │   ├── animal-measurement.routes.ts
│   │   │   ├── animal-measurement.model.ts
│   │   │   ├── animal-measurement.schema.ts
│   │   │   ├── animal-measurement.service.ts
│   │   │   └── animal-measurement.serializer.ts
│   │   ├── auth/                      # Authentication endpoints
│   │   │   ├── index.ts
│   │   │   ├── auth.routes.ts
│   │   │   ├── auth.schema.ts
│   │   │   └── auth.service.ts
│   │   ├── breed/                     # Animal breed management
│   │   │   ├── index.ts
│   │   │   ├── breed.routes.ts
│   │   │   ├── breed.model.ts
│   │   │   ├── breed.schema.ts
│   │   │   ├── breed.service.ts
│   │   │   └── breed.serializer.ts
│   │   ├── farm/                      # Farm management
│   │   │   ├── index.ts
│   │   │   ├── farm.routes.ts
│   │   │   ├── farm.model.ts
│   │   │   ├── farm.schema.ts
│   │   │   ├── farm.service.ts
│   │   │   └── farm.serializer.ts
│   │   ├── farm-member/               # Farm membership
│   │   │   ├── index.ts
│   │   │   ├── farm-member.routes.ts
│   │   │   ├── farm-member.model.ts
│   │   │   ├── farm-member.schema.ts
│   │   │   ├── farm-member.service.ts
│   │   │   └── farm-member.serializer.ts
│   │   ├── invitation/                # Farm invitations
│   │   │   ├── index.ts
│   │   │   ├── invitation.routes.ts
│   │   │   ├── invitation.model.ts
│   │   │   ├── invitation.schema.ts
│   │   │   ├── invitation.service.ts
│   │   │   └── invitation.serializer.ts
│   │   ├── species/                   # Animal species
│   │   │   ├── index.ts
│   │   │   ├── species.routes.ts
│   │   │   ├── species.model.ts
│   │   │   ├── species.schema.ts
│   │   │   ├── species.service.ts
│   │   │   └── species.serializer.ts
│   │   ├── species-translation/       # I18n translations
│   │   │   ├── index.ts
│   │   │   ├── species-translation.routes.ts
│   │   │   ├── species-translation.model.ts
│   │   │   ├── species-translation.schema.ts
│   │   │   ├── species-translation.service.ts
│   │   │   └── species-translation.serializer.ts
│   │   └── user/                      # User management
│   │       ├── index.ts
│   │       ├── user.routes.ts
│   │       ├── user.model.ts
│   │       ├── user.schema.ts
│   │       ├── user.service.ts
│   │       └── user.serializer.ts
│   ├── services/                      # Base service classes
│   │   └── base.service.ts            # BaseService with common CRUD operations
│   ├── utils/                         # Utility functions
│   │   ├── handle-sequelize-errors.ts # Database error handling
│   │   ├── id-hash-util.ts           # ID encoding/decoding (hashids)
│   │   ├── include-parser.ts         # Query include parsing
│   │   ├── order-parser.ts           # Query order parsing
│   │   ├── password-util.ts          # Password hashing utilities
│   │   ├── schema-builder.ts         # Schema building helpers
│   │   └── token-util.ts             # JWT token utilities
│   └── migrations/                    # Database migrations
│       ├── 20240607153000-user-model-migration.js
│       ├── 20240608180000-species-model-migration.js
│       ├── 20240609180000-user-language-migration.js
│       ├── 20250510115446-species-translation-migration.js
│       ├── 20250510121207-species-translation-unique-name-migration.js
│       ├── 20250510121728-species-translation-unique-name-language-migration.js
│       ├── 20250510182019-species-translation-language-enum-migration.js
│       ├── 20250510190000-farm-model-migration.js
│       ├── 20250510191000-user-last-visited-farm-migration.js
│       ├── 20250510192000-farm-members-migration.js
│       ├── 20250514180000-farm-invitation-model-migration.js
│       ├── 20250518180000-breed-model-migration.js
│       ├── 20250518200000-animal-model-migration.js
│       ├── 20250628094843-animal-parentid-to-fatherid-migration.js
│       ├── 20250703220000-animal-unique-tag-per-farm-species-migration.js
│       ├── 20250711000000-create-animal-measurements-table-migration.js
│       ├── 20250711000001-create-weight-sync-trigger-migration.js
│       ├── 20250724110843-update-animal-fields-constraints-migration.js
│       ├── 20250725000000-update-animal-models-refactor-migration.js
│       └── 20250725100000-remove-weight-sync-trigger-migration.js
├── src/seeders/                       # Database seed data
│   ├── 1-species-demo-data-seeder.js  # Species seed data
│   └── 2-breed-demo-data-seeder.js    # Breed seed data
├── little-sheep/                      # Bruno API testing collection
│   └── farm/
│       └── farm-animals/
│           └── create-animal.bru      # API test files
├── docs/                              # Documentation
│   └── architecture/                  # Architecture documentation
│       ├── architecture.md            # Plugin-based architecture overview
│       ├── tech-stack.md             # Technology stack details
│       ├── coding-standards.md       # Legacy coding standards
│       ├── coding-standards-v2.md    # New plugin-based coding standards
│       ├── source-tree.md            # Legacy source tree
│       └── source-tree-v2.md         # This document (new structure)
├── docker-compose.yml                 # Development environment
├── dockerfile                         # Container build configuration
├── package.json                       # Node.js dependencies & scripts
├── tsconfig.json                     # TypeScript configuration
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore rules
└── README.md                         # Project documentation
```

## Architecture Overview

### Core Application Structure
- **`server.ts`**: Application bootstrap with plugin registration and autoloading
- **`database/`**: Centralized database configuration and connection management
- **`plugins/`**: Core Fastify plugins for cross-cutting concerns
- **`resources/`**: Business domain resources following plugin pattern
- **`services/`**: Base service classes and common business logic
- **`utils/`**: Shared utility functions and helpers

### Plugin Loading Strategy

#### 1. Core Plugins (Manual Registration)
Loaded in specific order in `server.ts`:
1. **Database Plugin** - Establishes database connection
2. **Services Plugin** - Registers all services as decorators
3. **Authentication Plugin** - Provides JWT authentication
4. **Custom Reply Plugin** - Adds `reply.success()` and `reply.error()` methods
5. **Error Handler** - Global error handling and validation

#### 2. Resource Plugins (Autoloaded)
- Automatically discovered from `/src/resources/` directory
- Each resource directory must have an `index.ts` file
- Loaded with `/api/v1` prefix
- Route prefixes applied at plugin level

## Resource Structure Pattern

Each resource follows a consistent 6-file pattern:

### Required Files
1. **`index.ts`** - Plugin entry point and route registration
2. **`{resource}.routes.ts`** - HTTP route definitions
3. **`{resource}.model.ts`** - Sequelize database model
4. **`{resource}.schema.ts`** - Request/response validation schemas
5. **`{resource}.service.ts`** - Business logic and data operations
6. **`{resource}.serializer.ts`** - Response data transformation

### File Responsibilities

#### Plugin Entry (`index.ts`)
```typescript
import { FastifyPluginAsync } from 'fastify';
import resourceRoutes from './resource.routes';

const resourcePlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(resourceRoutes, { prefix: '/resources' });
};

export default resourcePlugin;
```

#### Routes (`{resource}.routes.ts`)
- HTTP endpoint definitions
- Middleware application (authentication, validation)
- Request/response handling
- Delegates business logic to services

#### Model (`{resource}.model.ts`)
- Sequelize model definition
- Database schema definition
- Getter methods for data access
- No associations (handled centrally)

#### Schema (`{resource}.schema.ts`)
- TypeBox/JSON Schema validation definitions
- Request body, query parameters, and response schemas
- Input validation and type coercion rules

#### Service (`{resource}.service.ts`)
- Business logic implementation
- Data access operations
- Cross-resource communication
- Extends BaseService for common CRUD operations

#### Serializer (`{resource}.serializer.ts`)
- Response data transformation
- ID encoding/decoding
- Data formatting and filtering
- Consistent API response structure

## Database Management

### Models & Associations
- **Models**: Defined within each resource directory
- **Associations**: Centralized in `/src/database/index.ts`
- **Migrations**: Versioned in `/src/migrations/` with timestamp ordering
- **Seeds**: Demo data in `/src/seeders/`

### Connection Management
- **Configuration**: `/src/database/sequelize-config.js`
- **Plugin**: `/src/database/database.plugin.ts`
- **Initialization**: Automatic connection and model sync

## Service Architecture

### BaseService Pattern
- Common CRUD operations (`findAll`, `findById`, `create`, `update`, `delete`)
- Consistent error handling
- Query building utilities
- Pagination support

### Service Registration
All services registered as Fastify decorators in `services.plugin.ts`:
```typescript
fastify.decorate('animalService', new AnimalService());
fastify.decorate('farmService', new FarmService());
// ... other services
```

### Service Usage in Routes
```typescript
// Access via Fastify decorator
const animals = await fastify.animalService.findAll();
```

## Naming Conventions

### Directory & File Naming
- **Resources**: `kebab-case` (e.g., `animal-measurement`)
- **Files**: `{resource-name}.{type}.ts` (e.g., `animal.service.ts`)
- **Models**: `PascalCase` classes (e.g., `AnimalMeasurement`)
- **Services**: `{Resource}Service` (e.g., `AnimalMeasurementService`)

### Database Conventions
- **Tables**: `snake_case` plural (e.g., `animal_measurements`)
- **Columns**: `snake_case` (e.g., `measured_at`, `animal_id`)
- **Indexes**: `idx_{table}_{columns}`
- **Foreign Keys**: `{table_singular}_id`

## API Structure

### URL Patterns
```
/api/v1/{resource}                    # Resource collection
/api/v1/{resource}/{id}               # Specific resource
/api/v1/farms/{farmId}/{resource}     # Farm-scoped resources
```

### Response Format
```json
{
  "status": "success",
  "data": { /* serialized resource data */ }
}
```

### Error Format
```json
{
  "status": "error",
  "error": "Error Type",
  "message": "Human readable message",
  "details": { /* additional error context */ }
}
```

## Development Workflow

### Adding New Resources
1. Create resource directory in `/src/resources/`
2. Implement all 6 required files
3. Create database migration
4. Register service in `services.plugin.ts`
5. Add TypeScript declarations if needed
6. Write tests
7. Update documentation

### Database Changes
1. Create migration file with timestamp
2. Update model definition
3. Run migration in development
4. Test both `up` and `down` migrations
5. Update service/schema as needed

## Key Architectural Benefits

### 1. **Modularity**
- Self-contained resources
- Clear separation of concerns
- Easy feature addition/removal

### 2. **Scalability**
- Automatic resource discovery
- Plugin-based architecture
- Microservice-ready structure

### 3. **Maintainability**
- Consistent file patterns
- Centralized configuration
- Standardized error handling

### 4. **Developer Experience**
- Hot reloading in development
- TypeScript support throughout
- Clear dependency injection

### 5. **Testing**
- Isolated plugin testing
- Service mocking via decorators
- Consistent API patterns

## Technology Stack Integration

### Core Technologies
- **Fastify 5.3.2** - Web framework with plugin system
- **TypeScript 5.8.3** - Type safety and developer experience
- **Sequelize 6.37.7** - ORM with PostgreSQL
- **PostgreSQL 14** - Primary database

### Key Libraries
- **@fastify/autoload** - Automatic plugin discovery
- **@sinclair/typebox** - Schema validation
- **hashids** - ID encoding/obfuscation
- **jsonwebtoken** - JWT authentication
- **bcryptjs** - Password hashing

### Development Tools
- **Bruno** - API testing collection
- **Docker Compose** - Development environment
- **nodemon** - Hot reloading
- **ts-node** - TypeScript execution

This new source tree structure reflects the major architectural refactor to a plugin-based system, providing better organization, scalability, and developer experience while maintaining the core business functionality of the livestock management system.