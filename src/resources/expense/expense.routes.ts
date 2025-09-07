import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { ExpenseCreate, ExpenseUpdate, ExpenseQuery, ExpenseParams, createExpenseSchema, listExpensesSchema, getExpenseSchema, updateExpenseSchema, deleteExpenseSchema } from './expense.schema';
import { ExpenseSerializer } from './expense.serializer';
import { decodeId } from '../../utils/id-hash-util';

const expenseRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	// GET /expenses - List all expenses for a farm
	fastify.get('/', {
		schema: listExpensesSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Querystring: ExpenseQuery }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const expenses = await fastify.expenseService.getExpenses(farmId, request.query);
			const serializedExpenses = ExpenseSerializer.serializeMany(expenses);
			reply.success(serializedExpenses);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// GET /expenses/:id - Get a single expense
	fastify.get('/:id', {
		schema: getExpenseSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: ExpenseParams }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const expenseId = decodeId(request.params.id);
			const expense = await fastify.expenseService.getExpenseById(expenseId!, farmId);

			if (!expense) {
				return reply.notFound('Expense not found');
			}

			const serializedExpense = ExpenseSerializer.serialize(expense);
			reply.success(serializedExpense);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// POST /expenses - Create a new expense
	fastify.post('/', {
		schema: createExpenseSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Body: ExpenseCreate }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const userId = request.user!.id;

			const expense = await fastify.expenseService.createExpense({
				...request.body,
				farmId,
				createdBy: userId,
			});

			const serializedExpense = ExpenseSerializer.serialize(expense);
			reply.success(serializedExpense);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// PUT /expenses/:id - Update an expense
	fastify.put('/:id', {
		schema: updateExpenseSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: ExpenseParams; Body: ExpenseUpdate }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const expenseId = decodeId(request.params.id);

			const expense = await fastify.expenseService.updateExpense(expenseId!, farmId, request.body);

			if (!expense) {
				return reply.notFound('Expense not found');
			}

			const serializedExpense = ExpenseSerializer.serialize(expense);
			reply.success(serializedExpense);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// DELETE /expenses/:id - Delete an expense
	fastify.delete('/:id', {
		schema: deleteExpenseSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: ExpenseParams }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const expenseId = decodeId(request.params.id);

			const deleted = await fastify.expenseService.deleteExpense(expenseId!, farmId);

			if (!deleted) {
				return reply.notFound('Expense not found');
			}

			reply.success({ message: 'Expense deleted successfully' });
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default expenseRoutes;
