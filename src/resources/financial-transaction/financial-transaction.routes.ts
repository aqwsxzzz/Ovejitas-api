import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	FinancialTransactionCreate,
	FinancialTransactionUpdate,
	FinancialTransactionQuery,
	FinancialTransactionParams,
	FinancialTransactionSummaryQuery,
	createFinancialTransactionSchema,
	listFinancialTransactionsSchema,
	getFinancialTransactionSchema,
	updateFinancialTransactionSchema,
	deleteFinancialTransactionSchema,
	summaryFinancialTransactionSchema,
} from './financial-transaction.schema';
import { FinancialTransactionSerializer } from './financial-transaction.serializer';
import { decodeId } from '../../utils/id-hash-util';
import { parsePagination } from '../../utils/pagination';

const financialTransactionRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	// GET /financial/summary - Get financial summary with aggregations
	fastify.get('/summary', {
		schema: summaryFinancialTransactionSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Querystring: FinancialTransactionSummaryQuery }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const summary = await fastify.financialTransactionService.getSummary(farmId, request.query);
			reply.success(summary);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// GET /financial - List all financial transactions for a farm
	fastify.get('/', {
		schema: listFinancialTransactionsSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Querystring: FinancialTransactionQuery }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const pagination = parsePagination(request.query);
			const result = await fastify.financialTransactionService.getTransactions(farmId, request.query, pagination);
			const serialized = FinancialTransactionSerializer.serializeMany(result.rows);
			reply.successWithPagination(serialized, result.pagination);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// GET /financial/:id - Get a single financial transaction
	fastify.get('/:id', {
		schema: getFinancialTransactionSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: FinancialTransactionParams }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const transactionId = decodeId(request.params.id);
			const transaction = await fastify.financialTransactionService.getTransactionById(transactionId!, farmId);

			if (!transaction) {
				return reply.notFound('Financial transaction not found');
			}

			const serialized = FinancialTransactionSerializer.serialize(transaction);
			reply.success(serialized);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// POST /financial - Create a new financial transaction
	fastify.post('/', {
		schema: createFinancialTransactionSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Body: FinancialTransactionCreate }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const userId = request.user!.id;

			const transaction = await fastify.financialTransactionService.createTransaction({
				...request.body,
				farmId,
				createdBy: userId,
			});

			const serialized = FinancialTransactionSerializer.serialize(transaction);
			reply.success(serialized);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// PUT /financial/:id - Update a financial transaction
	fastify.put('/:id', {
		schema: updateFinancialTransactionSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: FinancialTransactionParams; Body: FinancialTransactionUpdate }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const transactionId = decodeId(request.params.id);

			const transaction = await fastify.financialTransactionService.updateTransaction(transactionId!, farmId, request.body);

			if (!transaction) {
				return reply.notFound('Financial transaction not found');
			}

			const serialized = FinancialTransactionSerializer.serialize(transaction);
			reply.success(serialized);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	// DELETE /financial/:id - Delete a financial transaction
	fastify.delete('/:id', {
		schema: deleteFinancialTransactionSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: FinancialTransactionParams }>, reply) => {
		try {
			const farmId = request.lastVisitedFarmId;
			const transactionId = decodeId(request.params.id);

			const deleted = await fastify.financialTransactionService.deleteTransaction(transactionId!, farmId);

			if (!deleted) {
				return reply.notFound('Financial transaction not found');
			}

			reply.success({ message: 'Financial transaction deleted successfully' });
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default financialTransactionRoutes;
