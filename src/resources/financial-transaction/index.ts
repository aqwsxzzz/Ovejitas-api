import { FastifyPluginAsync } from 'fastify';
import financialTransactionRoutes from './financial-transaction.routes';

const financialTransactionPlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(financialTransactionRoutes, { prefix: '/financial' });
};

export default financialTransactionPlugin;
