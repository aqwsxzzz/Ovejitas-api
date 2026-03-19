import Fastify, { FastifyInstance, FastifyServerOptions } from 'fastify';
import fastifyAutoload from '@fastify/autoload';
import fastifyCookie from '@fastify/cookie';
import path from 'path';
import cors from '@fastify/cors';

// Core plugins
import customReplyPlugin from './plugins/custom-reply.plugin';
import errorHandler from './plugins/error-handler';
import databasePlugin from './database/database.plugin';
import servicesPlugin from './plugins/services.plugin';
import authenticationPlugin from './plugins/authentication-plugin';

export async function buildApp(opts?: FastifyServerOptions): Promise<FastifyInstance> {
	const server = Fastify({
		trustProxy: process.env.NODE_ENV === 'production',
		ajv: {
			customOptions: {
				removeAdditional: false,
				useDefaults: true,
				coerceTypes: true,
				strictTypes: false,
				allErrors: true,
			},
		},
		...opts,
	});

	const allowedOrigins = process.env.ALLOWED_ORIGINS
		? process.env.ALLOWED_ORIGINS.split(',')
		: ['http://localhost:5173', 'https://ovejitas.onrender.com'];

	server.register(cors, {
		origin: (origin, cb) => {
			if (!origin) return cb(null, true);

			if (allowedOrigins.includes(origin)) {
				cb(null, true);
			} else {
				cb(null, false);
			}
		},
		credentials: true,
		methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
		allowedHeaders: [
			'Accept',
			'Content-Type',
			'Authorization',
			'Origin',
			'X-Requested-With',
			'Cookie',
		],
		exposedHeaders: ['set-cookie'],
	});

	// Register core plugins
	server.register(databasePlugin);
	server.register(fastifyCookie);
	server.register(customReplyPlugin);
	server.register(errorHandler);
	server.register(servicesPlugin);
	server.register(authenticationPlugin);

	// Auto-load all resource plugins
	server.register(fastifyAutoload, {
		dir: path.join(__dirname, 'resources'),
		options: { prefix: '/api/v1' },
		matchFilter: (path) => path.endsWith('index.ts') || path.endsWith('index.js'),
		// @ts-expect-error this will work and skip directories without index.ts
		dirNameRoutePrefix: false,
	});

	// Error handler for validation errors
	server.setErrorHandler((error, _request, reply) => {
		server.log.error(error);

		if (error.validation) {
			const additionalPropsErrors = error.validation.filter(
				(err: { keyword: string }) => err.keyword === 'additionalProperties',
			);

			if (additionalPropsErrors.length > 0) {
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

	return server;
}
