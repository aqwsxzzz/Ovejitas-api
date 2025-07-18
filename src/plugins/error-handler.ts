// plugins/errorHandler.ts
import fp from 'fastify-plugin';
import { FastifyInstance, FastifyReply } from 'fastify';
import { handleAllErrors } from '../utils/handle-sequelize-errors';
import { ErrorMessage } from '../consts/error-messages';

export default fp(async function errorHandlingPlugin(fastify: FastifyInstance) {
	// Register the error handler
	fastify.decorate('handleDbError', function(error: unknown, reply: FastifyReply) {
		const errorResponse = handleAllErrors(error);

		// Log error for debugging (you might want to use a proper logger)
		if (errorResponse.status >= 500) {
			console.error('Server error:', error);
		}

		return reply.error(errorResponse.message as ErrorMessage, errorResponse.status);
	});

	// Optional: Global error handler for unhandled errors
	fastify.setErrorHandler((error, request, reply) => {
		const errorResponse = handleAllErrors(error);

		// Log error for debugging
		if (errorResponse.status >= 500) {
			console.error('Unhandled error:', error);
		}

		return reply.error(errorResponse.message as ErrorMessage, errorResponse.status);
	});
});
