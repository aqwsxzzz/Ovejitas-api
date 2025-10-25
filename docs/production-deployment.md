# Production Deployment Guide

This guide explains how to deploy the Ovejitas API to production environments, specifically focusing on Render deployment with Supabase as the database.

## Supabase Database Connection

### Overview

Supabase uses IPv6 by default on direct connections, which can cause issues with hosting platforms like Render that don't fully support IPv6. To resolve this, use Supabase's **Session Pooler** which provides IPv4 compatibility.

### Connection Modes

Supabase provides three connection string types:

1. **Direct Connection** (IPv6, not recommended for Render)
   ```
   postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.com:5432/postgres
   ```

2. **Session Pooler** (IPv4, recommended for persistent servers) ✅
   ```
   postgres://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
   ```

3. **Transaction Pooler** (IPv4, for serverless/edge functions)
   ```
   postgres://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```

### Why Session Pooler?

- **IPv4 Compatible**: Works on platforms without IPv6 support (like Render)
- **Prepared Statements**: Supports prepared statements (Transaction mode doesn't)
- **Persistent Connections**: Optimized for long-lived server connections
- **SSL Enabled**: Secure connections by default

## Render Environment Variables

Configure the following environment variables in your Render dashboard:

### Required Variables

```bash
# Database Configuration - Use Supabase Session Pooler
DB_HOST=aws-0-YOUR_REGION.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres.YOUR_PROJECT_REF
DB_PASS=YOUR_SUPABASE_PASSWORD

# JWT Configuration
JWT_SECRET=your-production-jwt-secret

# Environment
NODE_ENV=production

# CORS Configuration
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com

# Server Configuration
PORT=8080
HOST=0.0.0.0
```

### Optional Variables

```bash
# Cookie Domain (for cross-subdomain cookies)
COOKIE_DOMAIN=.yourdomain.com
```

### Variables You DON'T Need

- ❌ `DB_FORCE_IPV4` - Not needed with Session Pooler
- ❌ `DB_SSL_DISABLED` - Always use SSL in production
- ❌ `DATABASE_URL` - We use individual parameters

## Getting Supabase Connection Details

1. Go to your Supabase project dashboard
2. Navigate to **Settings** → **Database**
3. Under **Connection string**, select **Session pooler**
4. Copy the connection string (it will look like the Session Pooler format above)
5. Extract the individual components:
   - `DB_HOST`: The hostname (e.g., `aws-0-us-east-1.pooler.supabase.com`)
   - `DB_PORT`: Always `5432` for Session Pooler
   - `DB_NAME`: Always `postgres`
   - `DB_USER`: Format is `postgres.YOUR_PROJECT_REF`
   - `DB_PASS`: Your database password

## SSL/TLS Configuration

The application automatically enables SSL for all connections **unless** `DB_SSL_DISABLED=true` is set.

### Production SSL (Automatic)

```typescript
// Automatically configured when DB_SSL_DISABLED is not set
dialectOptions: {
  ssl: {
    require: true,
    rejectUnauthorized: false,
  },
}
```

### Local Development (Optional)

For local Docker development, you can disable SSL:

```bash
DB_SSL_DISABLED=true
```

## Connection Pool Configuration

The application uses the following connection pool settings (defined in `src/database/index.ts`):

```typescript
pool: {
  max: 5,        // Maximum connections in pool
  min: 0,        // Minimum connections in pool
  acquire: 30000, // Maximum time (ms) to acquire connection
  idle: 10000,   // Maximum idle time (ms) before release
}
```

These settings are optimized for typical web server workloads and work well with Supabase's connection limits.

## Deployment Checklist

- [ ] Set all required environment variables in Render
- [ ] Use Supabase **Session Pooler** connection string (port 5432)
- [ ] Verify `NODE_ENV=production`
- [ ] Configure CORS with actual frontend domains
- [ ] Generate a strong `JWT_SECRET` (use a random string generator)
- [ ] Do NOT set `DB_SSL_DISABLED` in production
- [ ] Do NOT set `DB_FORCE_IPV4` (not needed with pooler)
- [ ] Test database connection after deployment

## Troubleshooting

### Connection Timeouts

If you experience connection timeouts:

1. Verify you're using the **Session Pooler** (port 5432, not 6543)
2. Check that `DB_HOST` ends with `.pooler.supabase.com`
3. Verify your Supabase password is correct
4. Check Render logs for specific error messages

### SSL/TLS Errors

If you see SSL certificate errors:

1. Ensure `DB_SSL_DISABLED` is NOT set in production
2. Verify you're using the pooler hostname (not the direct `db.*.supabase.co` hostname)

### "Too Many Connections" Errors

If you hit connection limits:

1. Check your Supabase plan's connection limit
2. Consider reducing the `max` pool size in `src/database/index.ts`
3. Monitor connection usage in Supabase dashboard

## Local Development

For local development with Docker:

```bash
DB_HOST=postgres
DB_PORT=5432
DB_NAME=sheep
DB_USER=postgres
DB_PASS=postgres
DB_SSL_DISABLED=true
NODE_ENV=development
```

See `.env.example` for complete local development configuration.

## References

- [Supabase Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Render Environment Variables](https://render.com/docs/configure-environment-variables)
- [Sequelize PostgreSQL Documentation](https://sequelize.org/docs/v6/other-topics/dialect-specific-things/#postgresql)
