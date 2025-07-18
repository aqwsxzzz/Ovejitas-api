
import Fastify, { FastifyInstance } from 'fastify';
import fastifyCookie from '@fastify/cookie';
import fastifyCors from '@fastify/cors';
import './models/associations';
import customReplyPlugin from './plugins/custom-reply.plugin';
import errorHandler from './plugins/error-handler';
import databasePlugin from './database/database.plugin';
import userPlugin from './resources/user/user.plugin';
import authPlugin from './resources/auth/auth.plugin';

const server: FastifyInstance = Fastify({
	logger: true,
});

server.register(fastifyCors, {
	origin: ['http://localhost:5173'],
	credentials: true,
	methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
});

server.register(databasePlugin);
server.register(fastifyCookie);
server.register(customReplyPlugin);
server.register(errorHandler);

server.register(userPlugin, { prefix: '/api/v1' });
server.register(authPlugin, { prefix: '/api/v1' });

//Error handler for validation errors
server.setErrorHandler((error, request, reply) => {
	server.log.error(error);

	if (error.validation) {
		reply.status(400).send({
			error: 'Validation Error',
			message: error.message,
			details: error.validation,
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
