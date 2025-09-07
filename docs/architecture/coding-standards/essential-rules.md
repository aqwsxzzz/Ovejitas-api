# Essential Rules

1. **Always use TypeBox** for schemas and generate Static types
2. **Use `declare`** in models (no getters)
3. **Extend BaseService** for all services
4. **Encode/decode IDs** using `id-hash-util`
5. **Use schema-builder utilities** for endpoint schemas
6. **Handle errors** with `fastify.handleDbError(error, reply)`
7. **Wrap complex operations** in transactions
8. **Type requests** when accessing body/params
9. **Use farm scoping** with `request.lastVisitedFarmId`
10. **Serialize all responses** consistently
