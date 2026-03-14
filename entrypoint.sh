#!/bin/sh
set -e

echo "Running migrations..."
npx sequelize-cli db:migrate

echo "Running seeders..."
npx sequelize-cli db:seed:all

echo "Starting app..."
exec npx nodemon --config nodemon.json --legacy-watch
