import { FastifyPluginAsync } from 'fastify';
import expenseRoutes from './expense.routes';

const expensePlugin: FastifyPluginAsync = async (fastify) => {
	await fastify.register(expenseRoutes, { prefix: '/expenses' });
};

export default expensePlugin;
