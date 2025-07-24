
import Fastify, { FastifyInstance } from 'fastify';
import fastifyCookie from '@fastify/cookie';
import fastifyCors from '@fastify/cors';
import customReplyPlugin from './plugins/custom-reply.plugin';
import errorHandler from './plugins/error-handler';
import databasePlugin from './database/database.plugin';
import userPlugin from './resources/user/user.plugin';
import authPlugin from './resources/auth/auth.plugin';
import authenticationPlugin from './plugins/authentication-plugin';
import farmPlugin from './resources/farm/farm.plugin';
import farmMemberPlugin from './resources/farm-member/farm-member.plugin';
import invitationPlugin from './resources/invitation/invitation.plugin';
import speciesPlugin from './resources/species/species.plugin';
import breedPlugin from './resources/breed/breed.plugin';
import animalPlugin from './resources/animal/animal.plugin';

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

server.register(fastifyCors, {
	origin: ['http://localhost:5173'],
	credentials: true,
	methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
});

server.register(databasePlugin);
server.register(fastifyCookie);
server.register(customReplyPlugin);
server.register(errorHandler);
server.register(authenticationPlugin);

server.register(userPlugin, { prefix: '/api/v1' });
server.register(authPlugin, { prefix: '/api/v1' });
server.register(farmPlugin, { prefix: '/api/v1' });
server.register(farmMemberPlugin, { prefix: '/api/v1' });
server.register(invitationPlugin, { prefix: '/api/v1' });
server.register(speciesPlugin, { prefix: '/api/v1' });
server.register(breedPlugin, { prefix: '/api/v1' });
server.register(animalPlugin, { prefix: '/api/v1' });

//Error handler for validation errors
server.setErrorHandler((error, request, reply) => {
	server.log.error(error);

	if (error.validation) {

		// Check for additional properties errors
		const additionalPropsErrors = error.validation.filter(
			(err: {keyword: string}) => err.keyword === 'additionalProperties',
		);

		if (additionalPropsErrors.length > 0) {
			// Extract all additional property names
			const additionalProps = additionalPropsErrors.map(
				(err: {params?: {additionalProperty?: string}}) => err.params?.additionalProperty,
			).filter(Boolean);

			const message = additionalProps.length === 1
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
