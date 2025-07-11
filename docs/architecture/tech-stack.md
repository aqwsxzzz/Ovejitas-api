# Ovejitas-api Tech Stack

## Backend Technology Stack

### Core Runtime & Language
- **Node.js 18** (Alpine Linux) - JavaScript runtime environment
- **TypeScript 5.8.3** - Primary development language with strict type checking
- **ts-node 10.9.2** - TypeScript execution for development

### Web Framework & API
- **Fastify 5.3.2** - High-performance web framework
- **@fastify/cors** - Cross-origin resource sharing
- **@fastify/cookie** - Cookie handling for authentication

### Database & ORM
- **PostgreSQL 14** (Alpine) - Primary relational database
- **Sequelize 6.37.7** - Object-relational mapping
- **pg** - PostgreSQL client for Node.js

### Authentication & Security
- **jsonwebtoken 9.0.2** - JWT token generation and verification
- **bcryptjs 3.0.2** - Password hashing and verification
- **hashids 2.3.0** - ID obfuscation for public-facing identifiers

### Development Tools
- **nodemon 3.1.10** - Development server with hot reloading
- **dotenv** - Environment variable management
- **Bruno** - API testing and documentation collection

### Containerization
- **Docker** - Container runtime for development and deployment
- **Docker Compose** - Multi-container orchestration

## Technology Rationale

### Why Fastify over Express?
- **Performance**: 2x faster than Express in benchmarks
- **Built-in validation**: JSON Schema validation out of the box
- **TypeScript support**: Excellent TypeScript integration
- **Plugin ecosystem**: Robust plugin architecture

### Why PostgreSQL over NoSQL?
- **Data integrity**: ACID compliance for financial/livestock data
- **Relationships**: Complex relationships between farms, animals, species
- **Regulatory compliance**: Strong consistency for audit trails
- **Mature ecosystem**: Well-established tooling and expertise

### Why Sequelize over Prisma?
- **Existing codebase**: Already implemented with Sequelize
- **Migration system**: Robust migration and seeding capabilities
- **JavaScript compatibility**: Works well with existing JavaScript patterns
- **Flexibility**: Raw query capabilities when needed

### Why JWT over Sessions?
- **Stateless**: No server-side session storage required
- **Scalability**: Easy horizontal scaling
- **Multi-device**: Works across web, mobile, and API clients
- **Microservices ready**: Easy to validate across services

## Development Dependencies

### Type Definitions
- **@types/node** - Node.js type definitions
- **@types/bcryptjs** - bcryptjs type definitions
- **@types/jsonwebtoken** - JWT type definitions

### Database Tools
- **sequelize-cli** - Command-line interface for Sequelize
- **pg-types** - PostgreSQL type parsing

## Production Considerations

### Database Configuration
- **Connection pooling**: Configured for high concurrency
- **Read replicas**: Planned for read-heavy operations
- **Backup strategy**: Automated backups with point-in-time recovery

### Security Hardening
- **Helmet.js**: Security headers (planned)
- **Rate limiting**: Request throttling (planned)
- **Input sanitization**: SQL injection prevention via ORM

### Monitoring & Logging
- **Fastify logging**: Built-in Pino logger
- **Structured logging**: JSON format for log aggregation
- **Error tracking**: Centralized error reporting (planned)

## Version Pinning Strategy

All dependencies are pinned to specific versions to ensure:
- **Reproducible builds**: Same versions across environments
- **Security**: Known vulnerability status
- **Stability**: Tested compatibility matrix
- **Controlled updates**: Deliberate dependency updates

## Future Tech Stack Evolution

### Near-term Additions
- **Helmet.js** - Security headers
- **@fastify/rate-limit** - Request throttling
- **Winston** - Advanced logging (if needed)
- **Redis** - Caching and session storage (if needed)

### Long-term Considerations
- **GraphQL** - Alternative API layer
- **Bull** - Job queue for background tasks
- **Elasticsearch** - Search and analytics
- **Prometheus** - Metrics collection