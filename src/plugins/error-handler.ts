// plugins/errorHandler.ts
import fp from 'fastify-plugin';
import { FastifyReply } from 'fastify';
import { handleSequelizeError } from '../utils/handle-sequelize-errors';

export default fp(async function (fastify) {
	fastify.decorate('handleDbError', (error: unknown, reply: FastifyReply) => {
		const sequelizeError = handleSequelizeError(error);

		if (sequelizeError) {
			return reply.code(sequelizeError.status).send({
				message: sequelizeError.message,
				status: 'error',
			});
		}

		return reply.code(500).send({ error: 'Internal server error' });
	});
});
