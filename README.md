# Ovejitas API

REST API for livestock and farm management. Built with Fastify, Sequelize, TypeScript, and PostgreSQL.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

That's it. Everything runs in containers.

## Quick Start

```bash
# 1. Clone and enter the project
git clone git@github.com:aqwsxzzz/Ovejitas-api.git
cd Ovejitas-api

# 2. Create your .env file
cp .env.example .env
# Edit .env and set your own DB_USER, DB_PASS, and JWT_SECRET

# 3. Start the app
docker compose up

# 4. (Optional) Load demo data
docker compose exec app npm run dev:seed
```

The API will be available at `http://localhost:8081/api/v1`

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port (host-side) | `5436` |
| `DB_NAME` | Database name | `ovejitas` |
| `DB_USER` | Database user | - |
| `DB_PASS` | Database password | - |
| `JWT_SECRET` | Secret for JWT tokens | - |
| `PORT` | Server port | `8081` |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:5173` |
| `COOKIE_DOMAIN` | Cookie domain (production only) | - |

## Dev Seed

The dev seed script creates a full demo dataset for local development:

```bash
docker compose exec app npm run dev:seed
```

**Login:** `testuser@test.com` / `Password1`

Creates: 1 user, 1 farm, 15 animals (sheep, cattle, goats, pigs), 50 health measurements, and 17 expenses.

Idempotent - safe to run multiple times.

## Common Commands

All commands run inside Docker:

```bash
# Start (with logs)
docker compose up

# Start (detached)
docker compose up -d

# Run migrations
docker compose exec app npx sequelize-cli db:migrate

# Undo last migration
docker compose exec app npx sequelize-cli db:migrate:undo

# Run seeders
docker compose exec app npx sequelize-cli db:seed:all

# Build TypeScript
docker compose exec app npm run build

# Fresh start (wipe DB)
docker compose down -v
docker compose up
```

## API Endpoints

Base URL: `http://localhost:8081/api/v1`

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Register a new user |
| POST | `/auth/login` | Login (sets JWT cookie) |
| POST | `/auth/logout` | Logout (clears cookie) |
| GET | `/auth/me` | Get current user |
| GET | `/auth/health` | Health check |

### Farms
| Method | Endpoint | Description |
|---|---|---|
| POST | `/farms` | Create a farm |
| GET | `/farms` | List user's farms |
| GET | `/farms/:farmId` | Get farm (sets as active) |
| POST | `/farms/:farmId` | Update farm |
| DELETE | `/farms/:farmId` | Delete farm |

### Animals
| Method | Endpoint | Description |
|---|---|---|
| POST | `/animals` | Create an animal |
| POST | `/animals/bulk` | Bulk create animals |
| GET | `/animals` | List animals |
| GET | `/animals/:id` | Get animal by ID |
| PUT | `/animals/:id` | Update animal |
| DELETE | `/animals/:id` | Delete animal |
| GET | `/animals/dashboard` | Dashboard stats |

### Measurements
| Method | Endpoint | Description |
|---|---|---|
| POST | `/animals/:animalId/measurements` | Add measurement |
| GET | `/animals/:animalId/measurements` | List measurements |
| DELETE | `/animals/:animalId/measurements/:measurementId` | Delete measurement |

### Species & Breeds
| Method | Endpoint | Description |
|---|---|---|
| POST | `/species` | Create species |
| GET | `/species` | List species |
| GET | `/species/:id` | Get species |
| POST | `/species-translations` | Add species translation |
| POST | `/breeds` | Create breed |
| GET | `/breeds` | List breeds (requires `speciesId`) |
| POST | `/breed-translations` | Add breed translation |

### Expenses
| Method | Endpoint | Description |
|---|---|---|
| POST | `/expenses` | Create expense |
| GET | `/expenses` | List expenses |
| GET | `/expenses/:id` | Get expense |
| PUT | `/expenses/:id` | Update expense |
| DELETE | `/expenses/:id` | Delete expense |

### Farm Members & Invitations
| Method | Endpoint | Description |
|---|---|---|
| POST | `/farm-members` | Add member |
| GET | `/farm-members/:farmId/members` | List members |
| POST | `/invitations` | Send invitation |
| GET | `/invitations` | List invitations |
| POST | `/invitations/accept` | Accept invitation |

### Users
| Method | Endpoint | Description |
|---|---|---|
| PUT | `/users/:id` | Update user |
| DELETE | `/users/:id` | Delete user |

## Project Structure

```
src/
  resources/          # Feature modules (auto-loaded)
    animal/           # model, routes, schema, service, serializer
    auth/
    breed/
    expense/
    farm/
    species/
    ...
  plugins/            # Shared Fastify plugins
  services/           # Base service class
  migrations/         # Sequelize migrations (JS)
  seeders/            # Sequelize seeders (JS)
  scripts/            # Utility scripts (dev-seed)
  database/           # DB config and initialization
  utils/              # Shared utilities
  server.ts           # Entry point
```

## API Testing

API requests are documented in the `little-sheep/` directory as a [Bruno](https://www.usebruno.com/) collection.
