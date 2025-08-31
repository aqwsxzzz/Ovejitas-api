# Create Migration
npx sequelize-cli migration:generate --name animal-group-name --migrations-path src/migrations --config src/database/sequelize-config.js    

# Undo Migration
docker exec -it fastify-app npx sequelize-cli db:migrate:undo --migrations-path src/migrations --config src/database/sequelize-config.js