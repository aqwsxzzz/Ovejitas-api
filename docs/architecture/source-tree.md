# Ovejitas-api Source Tree

## Project Structure

```
ovejitas-api/
├── src/                            # Source code
│   ├── controllers/v1/             # HTTP request handlers
│   │   ├── auth.controller.ts      # Authentication endpoints
│   │   ├── user.controller.ts      # User management
│   │   ├── farm.controller.ts      # Farm operations
│   │   ├── animal.controller.ts    # Animal management
│   │   ├── species.controller.ts   # Species/breed management
│   │   └── invitation.controller.ts # Farm invitations
│   ├── routes/v1/                  # API route definitions
│   │   ├── auth.routes.ts          # Auth routes
│   │   ├── user.routes.ts          # User routes
│   │   ├── farm.routes.ts          # Farm routes
│   │   ├── animal.routes.ts        # Animal routes
│   │   ├── species.routes.ts       # Species routes
│   │   └── invitation.routes.ts    # Invitation routes
│   ├── models/                     # Database models
│   │   ├── user-model.ts           # User model
│   │   ├── farm-model.ts           # Farm model
│   │   ├── animal-model.ts         # Animal model
│   │   ├── species-model.ts        # Species model
│   │   ├── breed-model.ts          # Breed model
│   │   ├── farm-members-model.ts   # Farm membership
│   │   ├── farm-invitation-model.ts # Farm invitations
│   │   ├── species-translation-model.ts # I18n translations
│   │   ├── temporal/               # Temporal data models
│   │   └── associations.ts         # Model relationships
│   ├── schemas/                    # Validation schemas
│   │   ├── auth.schema.ts          # Auth validation
│   │   ├── user.schema.ts          # User validation
│   │   ├── farm.schema.ts          # Farm validation
│   │   ├── animal.schema.ts        # Animal validation
│   │   └── common.schema.ts        # Shared schemas
│   ├── serializers/                # Response formatting
│   │   ├── user.serializer.ts      # User responses
│   │   ├── farm.serializer.ts      # Farm responses
│   │   ├── animal.serializer.ts    # Animal responses
│   │   └── common.serializer.ts    # Shared serializers
│   ├── types/                      # TypeScript types
│   │   ├── auth.types.ts           # Auth types
│   │   ├── user.types.ts           # User types
│   │   ├── farm.types.ts           # Farm types
│   │   ├── animal.types.ts         # Animal types
│   │   └── common.types.ts         # Shared types
│   ├── utils/                      # Utility functions
│   │   ├── jwt.utils.ts            # JWT helpers
│   │   ├── password.utils.ts       # Password hashing
│   │   ├── validation.utils.ts     # Validation helpers
│   │   └── response.utils.ts       # Response formatting
│   ├── plugins/                    # Fastify plugins
│   │   ├── auth.plugin.ts          # Authentication
│   │   ├── db.plugin.ts            # Database connection
│   │   └── validation.plugin.ts    # Input validation
│   ├── migrations/                 # Database migrations
│   │   ├── 001-create-users.js     # User table
│   │   ├── 002-create-farms.js     # Farm table
│   │   ├── 003-create-species.js   # Species table
│   │   ├── 004-create-breeds.js    # Breed table
│   │   ├── 005-create-animals.js   # Animal table
│   │   └── 006-create-farm-members.js # Farm membership
│   ├── seeders/                    # Database seeds
│   │   ├── 001-species.js          # Species data
│   │   ├── 002-breeds.js           # Breed data
│   │   └── 003-demo-data.js        # Demo farms/animals
│   ├── config/                     # Configuration
│   │   ├── database.js             # DB configuration
│   │   └── environment.ts          # Environment vars
│   └── app.ts                      # Application entry point
├── little-sheep/                   # Bruno API collection
│   └── farm/
│       └── farm-animals/
│           └── create-animal.bru   # API test files
├── docs/                           # Documentation
│   ├── architecture.md             # System architecture
│   ├── tech-stack.md              # Technology choices
│   └── source-tree.md             # This document
├── docker-compose.yml              # Development environment
├── dockerfile                      # Container build
├── package.json                    # Dependencies
├── tsconfig.json                   # TypeScript config
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
└── README.md                       # Project documentation
```

## File Naming Conventions

### Models
- `{entity}-model.ts` - e.g., `user-model.ts`, `farm-model.ts`
- kebab-case with `-model` suffix
- Sequelize model classes inside

### Controllers
- `{entity}.controller.ts` - e.g., `user.controller.ts`
- kebab-case with `.controller` suffix

### Routes
- `{entity}.routes.ts` - e.g., `user.routes.ts`
- kebab-case with `.routes` suffix

### Schemas
- `{entity}.schema.ts` - e.g., `user.schema.ts`
- kebab-case with `.schema` suffix

### Types
- `{entity}.types.ts` - e.g., `user.types.ts`
- kebab-case with `.types` suffix

### Utilities
- `{functionality}.utils.ts` - e.g., `jwt.utils.ts`
- kebab-case with `.utils` suffix

## Tech Stack Summary

**Backend Stack**:
- **Node.js 18** + **TypeScript 5.8.3** + **Fastify 5.3.2**
- **PostgreSQL 14** + **Sequelize 6.37.7**
- **JWT authentication** + **bcryptjs password hashing**
- **Docker** development environment
- **Bruno** API testing collection

**Architecture Pattern**:
- **Layered monolithic** with clear separation of concerns
- **Multi-tenant** farm-based data isolation
- **RESTful API** with versioning (`/v1`)
- **Clean architecture** with controllers → services → models → database