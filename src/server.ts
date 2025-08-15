import Fastify, { FastifyInstance } from 'fastify';
import fastifyAutoload from '@fastify/autoload';
import fastifyCookie from '@fastify/cookie';
import fastifyCors from '@fastify/cors';
import path from 'path';

// Core plugins
import customReplyPlugin from './plugins/custom-reply.plugin';
import errorHandler from './plugins/error-handler';
import databasePlugin from './database/database.plugin';
import servicesPlugin from './plugins/services.plugin';
import authenticationPlugin from './plugins/authentication-plugin';

const server: FastifyInstance = Fastify({
	logger: true,
	ajv: {
		customOptions: {
			// Don't remove additional properties - instead throw validation errors
			removeAdditional: false,
			useDefaults: true,
			coerceTypes: true,
			strictTypes: false,
			// Ensure we validate additional properties
			allErrors: true,
		},
	},
});

// Register CORS
server.register(fastifyCors, {
	origin: ['http://localhost:5173', 'https://ovejitas.onrender.com'],
	credentials: true,
	methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
});

// Register core plugins
server.register(databasePlugin);
server.register(fastifyCookie);
server.register(customReplyPlugin);
server.register(errorHandler);
server.register(servicesPlugin); // Must be after database plugin
server.register(authenticationPlugin);

// Auto-load all resource plugins
server.register(fastifyAutoload, {
	dir: path.join(__dirname, 'resources'),
	options: { prefix: '/api/v1' },
	// Only load directories that have an index.ts file
	matchFilter: (path) => path.endsWith('index.ts') || path.endsWith('index.js'),
	// @ts-expect-error this will work and skip directories without index.ts
	dirNameRoutePrefix: false,
});

//Error handler for validation errors
server.setErrorHandler((error, _request, reply) => {
	server.log.error(error);

	if (error.validation) {
		// Check for additional properties errors
		const additionalPropsErrors = error.validation.filter(
			(err: { keyword: string }) => err.keyword === 'additionalProperties',
		);

		if (additionalPropsErrors.length > 0) {
			// Extract all additional property names
			const additionalProps = additionalPropsErrors
				.map((err: { params?: { additionalProperty?: string } }) => err.params?.additionalProperty)
				.filter(Boolean);

			const message =
				additionalProps.length === 1
					? `Additional property '${additionalProps[0]}' is not allowed`
					: `Additional properties not allowed: ${additionalProps.join(', ')}`;

			reply.status(400).send({
				error: 'Validation Error',
				message: message,
				details: error.validation,
				status: 'error',
			});
			return;
		}

		// Handle other validation errors
		reply.status(400).send({
			error: 'Validation Error',
			message: error.message,
			details: error.validation,
			status: 'error',
		});
		return;
	}

	reply.status(500).send({
		error: 'Internal Server Error',
		message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong',
	});
});

const start = async () => {
	try {
		await server.listen({ port: 8080, host: '0.0.0.0' });
		console.log(`Server is running at ${server.server.address()}`);

		console.log('📋 Registered routes:');
		console.log(server.printRoutes());
	} catch (err) {
		server.log.error(err);
		process.exit(1);
	}
};

start();
