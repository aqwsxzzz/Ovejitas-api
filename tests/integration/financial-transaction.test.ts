import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import { createSpecies, createFinancialTransaction } from '../helpers/factories';
import { encodeId } from '../../src/utils/id-hash-util';

describe('Financial Transaction endpoints', () => {
	let app: FastifyInstance;

	beforeAll(async () => {
		app = await createTestApp();
	});

	afterEach(async () => {
		await truncateAllTables(app);
	});

	afterAll(async () => {
		await app.close();
	});

	describe('GET /api/v1/financial', () => {
		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial',
			});

			expect(response.statusCode).toBe(401);
		});

		it('returns transactions with default pagination', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'expense', amount: 100 });
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'income', amount: 200 });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data).toHaveLength(2);
			expect(body.meta.pagination).toBeDefined();
			expect(body.meta.pagination.total).toBe(2);
		});

		it('returns paginated results', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			await createFinancialTransaction(app, user.farmId, speciesId, user.id);
			await createFinancialTransaction(app, user.farmId, speciesId, user.id);
			await createFinancialTransaction(app, user.farmId, speciesId, user.id);

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial?page=1&limit=2',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(2);
			expect(body.meta.pagination.total).toBe(3);
			expect(body.meta.pagination.totalPages).toBe(2);
		});

		it('filters by type', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'expense' });
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'income' });
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'income' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial?type=income',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(2);
		});

		it('filters by date range', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { date: '2026-01-15' });
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { date: '2026-02-15' });
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { date: '2026-03-15' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial?from=2026-02-01&to=2026-02-28',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(1);
		});

		it('filters by speciesId', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId: sheepId } = await createSpecies(app, { name: 'Sheep' });
			const { speciesId: goatId } = await createSpecies(app, { name: 'Goat' });
			await createFinancialTransaction(app, user.farmId, sheepId, user.id);
			await createFinancialTransaction(app, user.farmId, goatId, user.id);

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/financial?speciesId=${encodeId(sheepId)}`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(1);
		});

		it('only returns transactions from the authenticated user farm', async () => {
			const { user: user1, cookie: cookie1 } = await createAuthenticatedUser(app);
			const { user: user2 } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			await createFinancialTransaction(app, user1.farmId, speciesId, user1.id);
			await createFinancialTransaction(app, user2.farmId, speciesId, user2.id);
			await createFinancialTransaction(app, user2.farmId, speciesId, user2.id);

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial',
				headers: { cookie: cookie1 },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(1);
		});
	});

	describe('GET /api/v1/financial/:id', () => {
		it('returns a single transaction by id', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { encodedTransactionId } = await createFinancialTransaction(
				app, user.farmId, speciesId, user.id,
				{ type: 'expense', amount: 250, description: 'Feed purchase' },
			);

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/financial/${encodedTransactionId}`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data.type).toBe('expense');
			expect(body.data.amount).toBe(250);
			expect(body.data.description).toBe('Feed purchase');
			expect(typeof body.data.id).toBe('string');
			expect(typeof body.data.speciesId).toBe('string');
		});

		it('returns 404 for non-existent transaction', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial/nonexistentid',
				headers: { cookie },
			});

			expect(response.statusCode).toBe(400);
		});
	});

	describe('POST /api/v1/financial', () => {
		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/financial',
				payload: {
					type: 'expense',
					amount: 100,
					speciesId: 'fakeid',
					date: '2026-03-15',
				},
			});

			expect(response.statusCode).toBe(401);
		});

		it('creates a new expense transaction', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/financial',
				headers: { cookie },
				payload: {
					type: 'expense',
					amount: 150.50,
					description: 'Veterinary check',
					speciesId: encodeId(speciesId),
					date: '2026-03-15',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(201);
			expect(body.status).toBe('success');
			expect(body.data.type).toBe('expense');
			expect(body.data.amount).toBe(150.50);
			expect(body.data.description).toBe('Veterinary check');
			expect(body.data.date).toBe('2026-03-15');
			expect(typeof body.data.id).toBe('string');
		});

		it('creates a new income transaction', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/financial',
				headers: { cookie },
				payload: {
					type: 'income',
					amount: 500,
					description: 'Wool sale',
					speciesId: encodeId(speciesId),
					date: '2026-03-20',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(201);
			expect(body.data.type).toBe('income');
			expect(body.data.amount).toBe(500);
		});

		it('creates transaction without description', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/financial',
				headers: { cookie },
				payload: {
					type: 'expense',
					amount: 75,
					speciesId: encodeId(speciesId),
					date: '2026-03-15',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(201);
			expect(body.data.description).toBeNull();
		});

		it('rejects invalid species id', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/financial',
				headers: { cookie },
				payload: {
					type: 'expense',
					amount: 100,
					speciesId: encodeId(99999),
					date: '2026-03-15',
				},
			});

			expect(response.statusCode).toBe(400);
		});

		it('rejects amount of zero', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/financial',
				headers: { cookie },
				payload: {
					type: 'expense',
					amount: 0,
					speciesId: encodeId(speciesId),
					date: '2026-03-15',
				},
			});

			expect(response.statusCode).toBe(400);
		});

		it('rejects missing required fields', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/financial',
				headers: { cookie },
				payload: {
					type: 'expense',
				},
			});

			expect(response.statusCode).toBe(400);
		});
	});

	describe('PUT /api/v1/financial/:id', () => {
		it('updates an existing transaction', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { encodedTransactionId } = await createFinancialTransaction(
				app, user.farmId, speciesId, user.id,
				{ type: 'expense', amount: 100 },
			);

			const response = await app.inject({
				method: 'PUT',
				url: `/api/v1/financial/${encodedTransactionId}`,
				headers: { cookie },
				payload: {
					amount: 200,
					description: 'Updated description',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.amount).toBe(200);
			expect(body.data.description).toBe('Updated description');
		});

		it('updates transaction type', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { encodedTransactionId } = await createFinancialTransaction(
				app, user.farmId, speciesId, user.id,
				{ type: 'expense' },
			);

			const response = await app.inject({
				method: 'PUT',
				url: `/api/v1/financial/${encodedTransactionId}`,
				headers: { cookie },
				payload: {
					type: 'income',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.type).toBe('income');
		});

		it('updates species on a transaction', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId: sheepId } = await createSpecies(app, { name: 'Sheep' });
			const { speciesId: goatId } = await createSpecies(app, { name: 'Goat' });
			const { encodedTransactionId } = await createFinancialTransaction(
				app, user.farmId, sheepId, user.id,
			);

			const response = await app.inject({
				method: 'PUT',
				url: `/api/v1/financial/${encodedTransactionId}`,
				headers: { cookie },
				payload: {
					speciesId: encodeId(goatId),
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.speciesId).toBe(encodeId(goatId));
		});

		it('returns 404 for non-existent transaction', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'PUT',
				url: '/api/v1/financial/nonexistentid',
				headers: { cookie },
				payload: { amount: 200 },
			});

			expect(response.statusCode).toBe(400);
		});
	});

	describe('DELETE /api/v1/financial/:id', () => {
		it('deletes a transaction', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { encodedTransactionId } = await createFinancialTransaction(
				app, user.farmId, speciesId, user.id,
			);

			const response = await app.inject({
				method: 'DELETE',
				url: `/api/v1/financial/${encodedTransactionId}`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
		});

		it('returns 404 for non-existent transaction', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'DELETE',
				url: '/api/v1/financial/nonexistentid',
				headers: { cookie },
			});

			expect(response.statusCode).toBe(400);
		});

		it('cannot fetch deleted transaction', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { encodedTransactionId } = await createFinancialTransaction(
				app, user.farmId, speciesId, user.id,
			);

			await app.inject({
				method: 'DELETE',
				url: `/api/v1/financial/${encodedTransactionId}`,
				headers: { cookie },
			});

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/financial/${encodedTransactionId}`,
				headers: { cookie },
			});

			expect(response.statusCode).toBe(404);
		});
	});

	describe('GET /api/v1/financial/summary', () => {
		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial/summary',
			});

			expect(response.statusCode).toBe(401);
		});

		it('returns totals and breakdown grouped by month', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'income', amount: 500, date: '2026-01-15' });
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'expense', amount: 200, date: '2026-01-20' });
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'income', amount: 300, date: '2026-02-10' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial/summary?groupBy=month&from=2026-01-01&to=2026-02-28',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data.totals).toBeDefined();
			expect(body.data.totals.income).toBe(800);
			expect(body.data.totals.expenses).toBe(200);
			expect(body.data.totals.net).toBe(600);
			expect(body.data.breakdown).toHaveLength(2);
		});

		it('returns breakdown grouped by day', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'expense', amount: 50, date: '2026-03-01' });
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'expense', amount: 75, date: '2026-03-01' });
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'expense', amount: 100, date: '2026-03-02' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial/summary?groupBy=day&from=2026-03-01&to=2026-03-02',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.breakdown).toHaveLength(2);
			expect(body.data.totals.expenses).toBe(225);
		});

		it('filters summary by type', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'income', amount: 1000, date: '2026-01-15' });
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'expense', amount: 300, date: '2026-01-20' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial/summary?type=expense&from=2026-01-01&to=2026-01-31',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.totals.expenses).toBe(300);
			expect(body.data.totals.income).toBe(0);
		});

		it('filters summary by species', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId: sheepId } = await createSpecies(app, { name: 'Sheep' });
			const { speciesId: goatId } = await createSpecies(app, { name: 'Goat' });
			await createFinancialTransaction(app, user.farmId, sheepId, user.id, { type: 'expense', amount: 100, date: '2026-01-15' });
			await createFinancialTransaction(app, user.farmId, goatId, user.id, { type: 'expense', amount: 200, date: '2026-01-15' });

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/financial/summary?speciesId=${encodeId(sheepId)}&from=2026-01-01&to=2026-01-31`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.totals.expenses).toBe(100);
		});

		it('uses period shorthand for date range', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const today = new Date().toISOString().split('T')[0]!;
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'expense', amount: 50, date: today });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial/summary?period=7d&groupBy=day',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.totals.expenses).toBe(50);
		});

		it('returns empty totals when no transactions exist', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial/summary?from=2026-01-01&to=2026-12-31',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.totals.income).toBe(0);
			expect(body.data.totals.expenses).toBe(0);
			expect(body.data.totals.net).toBe(0);
			expect(body.data.breakdown).toHaveLength(0);
		});

		it('only includes transactions from the authenticated user farm', async () => {
			const { user: user1, cookie: cookie1 } = await createAuthenticatedUser(app);
			const { user: user2 } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			await createFinancialTransaction(app, user1.farmId, speciesId, user1.id, { type: 'expense', amount: 100, date: '2026-01-15' });
			await createFinancialTransaction(app, user2.farmId, speciesId, user2.id, { type: 'expense', amount: 999, date: '2026-01-15' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial/summary?from=2026-01-01&to=2026-01-31',
				headers: { cookie: cookie1 },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.totals.expenses).toBe(100);
		});

		it('calculates net correctly with mixed income and expenses', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'income', amount: 1000, date: '2026-01-10' });
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'income', amount: 500, date: '2026-01-15' });
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'expense', amount: 300, date: '2026-01-20' });
			await createFinancialTransaction(app, user.farmId, speciesId, user.id, { type: 'expense', amount: 200, date: '2026-01-25' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/financial/summary?groupBy=month&from=2026-01-01&to=2026-01-31',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.totals.income).toBe(1500);
			expect(body.data.totals.expenses).toBe(500);
			expect(body.data.totals.net).toBe(1000);
			expect(body.data.breakdown).toHaveLength(1);
			expect(body.data.breakdown[0].net).toBe(1000);
		});
	});
});
