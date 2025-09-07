# Ovejitas-api Source Tree

Plugin-based Fastify API for livestock management.

## Key Directories

```
src/
├── server.ts                    # App entry point
├── database/                    # DB config & connections
├── plugins/                     # Core Fastify plugins
├── resources/                   # Business logic (autoloaded)
│   └── {resource}/             # Each resource has 6 files:
│       ├── index.ts            #   Plugin entry
│       ├── {name}.routes.ts    #   HTTP routes
│       ├── {name}.model.ts     #   Sequelize model
│       ├── {name}.schema.ts    #   Validation schemas
│       ├── {name}.service.ts   #   Business logic
│       └── {name}.serializer.ts#   Response transform
├── services/base.service.ts     # Common CRUD operations
├── utils/                       # Shared utilities
└── migrations/                  # Database changes
```

## How It Works

**Plugin Architecture**: Fastify auto-loads resources from `/src/resources/`, each becoming a route plugin.

**Core Flow**: server.ts → plugins (DB, auth, services) → auto-load resources → ready

**Resource Pattern**: Every business feature gets its own directory with the same 6-file structure.

## Adding New Features

1. Create `/src/resources/my-feature/` directory
2. Copy the 6-file pattern from any existing resource
3. Update database with migration if needed
4. Register service in `services.plugin.ts`

See [coding standards](coding-standards.md) for implementation details.