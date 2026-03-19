# ---- Dev stage (used by docker-compose) ----
FROM node:20-slim AS dev
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# ---- Build stage ----
FROM dev AS build
RUN npm run build

# ---- Production stage ----
FROM node:20-slim AS production
WORKDIR /app
COPY --from=build /app/build ./build
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./
COPY --from=build /app/.sequelizerc ./
COPY --from=build /app/src/migrations ./src/migrations
COPY --from=build /app/src/seeders ./src/seeders
COPY --from=build /app/src/database/sequelize-config.js ./src/database/sequelize-config.js
COPY --chown=node:node entrypoint.prod.sh ./entrypoint.prod.sh
USER node
CMD ["sh", "entrypoint.prod.sh"]
