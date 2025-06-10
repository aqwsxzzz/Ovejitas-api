#!/bin/sh

# Run migrations
npx sequelize-cli db:migrate --migrations-path src/migrations --config src/config/sequelize-config.js

# Check if the database has already been seeded
if [ ! -f /app/.seeded ]; then
  echo "Seeding database..."
  npx sequelize-cli db:seed:all --seeders-path src/seeders --config src/config/sequelize-config.js

  # Mark as seeded
  touch /app/.seeded
else
  echo "Database already seeded. Skipping..."
fi

# Start the app
npx nodemon --config nodemon.json --legacy-watch
