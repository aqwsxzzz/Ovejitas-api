FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application source
COPY . .

# Build TypeScript code
RUN npm run build

# Runtime stage
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm ci --only=production

# Copy built application from build stage
COPY --from=build /app/build ./build

# Copy necessary files for runtime
COPY --from=build /app/node_modules ./node_modules

# Expose the application port
EXPOSE 8080

# Command to run the application
CMD ["node", "build/index.js"]

# Development stage
FROM node:18-alpine as dev

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies including dev dependencies
RUN npm install

# Copy application source
COPY . .

# Expose the application port
EXPOSE 8080

# Command to run the application with nodemon for development
CMD ["npm", "run", "dev"]