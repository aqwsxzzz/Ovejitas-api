# Production Deployment Guide

This guide explains how to deploy the Ovejitas API to Render with Render's managed PostgreSQL.

## Render PostgreSQL Setup

1. In your Render dashboard, create a new **PostgreSQL** instance
2. Note the connection details from the PostgreSQL dashboard (host, port, database, user, password)
3. SSL is enabled by default on Render PostgreSQL — the app handles this automatically when `NODE_ENV=production`

## Render Environment Variables

Configure the following environment variables in your Render web service:

### Required Variables

```bash
# Database Configuration — from Render PostgreSQL dashboard
DB_HOST=your-db-hostname.render.com
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASS=your_database_password

# JWT Configuration
JWT_SECRET=your-production-jwt-secret

# Environment
NODE_ENV=production

# CORS Configuration
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com

# Server Configuration
PORT=8081
HOST=0.0.0.0
```

### Optional Variables

```bash
# Cookie Domain (for cross-subdomain cookies)
COOKIE_DOMAIN=.yourdomain.com
```

## SSL/TLS Configuration

- **Production**: SSL is automatically enabled with `rejectUnauthorized: true` when `NODE_ENV=production`. Render's managed PostgreSQL uses valid certificates, so strict verification works out of the box.
- **Local Development**: No SSL is configured, since the local Docker PostgreSQL doesn't use it.

## Connection Pool Configuration

The application uses the following connection pool settings (defined in `src/database/index.ts`):

```typescript
pool: {
  max: 5,
  min: 0,
  acquire: 30000,
  idle: 10000,
}
```

These work well for Render's starter/standard tiers. Adjust `max` based on your Render PostgreSQL plan's connection limit.

## Deployment Checklist

- [ ] Create a Render PostgreSQL instance
- [ ] Set all required environment variables in the Render web service
- [ ] Verify `NODE_ENV=production`
- [ ] Configure CORS with actual frontend domains
- [ ] Generate a strong `JWT_SECRET`
- [ ] Test database connection after deployment

## Troubleshooting

### Connection Timeouts

1. Verify `DB_HOST` matches the hostname from the Render PostgreSQL dashboard
2. Ensure the web service and database are in the same Render region
3. Check Render logs for specific error messages

### SSL/TLS Errors

If you see SSL certificate errors, verify that `NODE_ENV=production` is set. The app only enables SSL in production mode.

### "Too Many Connections" Errors

1. Check your Render PostgreSQL plan's connection limit
2. Reduce the `max` pool size in `src/database/index.ts` if needed

## Local Development

For local development with Docker:

```bash
DB_HOST=postgres
DB_PORT=5436
DB_NAME=ovejitas
DB_USER=postgres
DB_PASS=postgres
NODE_ENV=development
```

See `.env.example` for complete local development configuration.

## References

- [Render PostgreSQL](https://docs.render.com/databases)
- [Render Environment Variables](https://docs.render.com/configure-environment-variables)
- [Sequelize PostgreSQL Documentation](https://sequelize.org/docs/v6/other-topics/dialect-specific-things/#postgresql)
