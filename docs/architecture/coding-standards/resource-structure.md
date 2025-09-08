# Resource Structure

Each business resource follows this exact 6-file pattern:

```
src/resources/{resource-name}/
├── index.ts                    # Plugin entry point
├── {resource}.routes.ts        # Route definitions
├── {resource}.model.ts         # Sequelize model
├── {resource}.schema.ts        # TypeBox schemas + types
├── {resource}.service.ts       # Business logic service
└── {resource}.serializer.ts    # Response transformation
```
