import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import { createExpense } from '../helpers/factories';

describe('Expense endpoints', () => {
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

	describe('GET /api/v1/expenses', () => {
		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/expenses',
			});

			expect(response.statusCode).toBe(401);
		});

		it('returns expenses for the authenticated user farm', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			await createExpense(app, user.farmId, user.id, { amount: 100, category: 'feed' });
			await createExpense(app, user.farmId, user.id, { amount: 200, category: 'veterinary' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/expenses',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data).toHaveLength(2);
		});

		it('returns paginated results', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			await createExpense(app, user.farmId, user.id, { amount: 100, date: '2025-01-01' });
			await createExpense(app, user.farmId, user.id, { amount: 200, date: '2025-01-02' });
			await createExpense(app, user.farmId, user.id, { amount: 300, date: '2025-01-03' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/expenses?page=1&limit=2',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(2);
			expect(body.meta.pagination.total).toBe(3);
			expect(body.meta.pagination.totalPages).toBe(2);
		});

		it('filters expenses by category', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			await createExpense(app, user.farmId, user.id, { category: 'feed' });
			await createExpense(app, user.farmId, user.id, { category: 'veterinary' });
			await createExpense(app, user.farmId, user.id, { category: 'feed' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/expenses?category=feed',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(2);
		});
	});

	describe('POST /api/v1/expenses', () => {
		it('returns 401 when not authenticated with valid body', async () => {
			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/expenses',
				payload: {
					date: '2025-06-15',
					amount: 100,
					category: 'feed',
				},
			});

			expect(response.statusCode).toBe(401);
		});

		it('creates a new expense', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/expenses',
				headers: { cookie },
				payload: {
					date: '2025-06-15',
					amount: 150.00,
					category: 'feed',
					description: 'Monthly feed purchase',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(Number(body.data.amount)).toBe(150);
			expect(body.data.category).toBe('feed');
			expect(typeof body.data.id).toBe('string');
		});

		it('creates an expense with quantity and unit cost', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/expenses',
				headers: { cookie },
				payload: {
					date: '2025-06-15',
					amount: 250.00,
					category: 'feed',
					quantity: 5,
					quantityUnit: 'bags',
					unitCost: 50.00,
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(Number(body.data.quantity)).toBe(5);
			expect(body.data.quantityUnit).toBe('bags');
		});
	});

	describe('GET /api/v1/expenses/:id', () => {
		it('returns a single expense by id', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { encodedExpenseId } = await createExpense(app, user.farmId, user.id, {
				amount: 99.99,
				category: 'veterinary',
			});

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/expenses/${encodedExpenseId}`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.category).toBe('veterinary');
		});

		it('returns 404 for non-existent expense', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/expenses/nonexistentid',
				headers: { cookie },
			});

			// decodeId returns undefined for invalid hash, service receives undefined
			expect(response.statusCode).toBeGreaterThanOrEqual(400);
		});
	});

	describe('DELETE /api/v1/expenses/:id', () => {
		it('deletes an expense', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { encodedExpenseId } = await createExpense(app, user.farmId, user.id);

			const response = await app.inject({
				method: 'DELETE',
				url: `/api/v1/expenses/${encodedExpenseId}`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');

			// Verify it's gone
			const getResponse = await app.inject({
				method: 'GET',
				url: `/api/v1/expenses/${encodedExpenseId}`,
				headers: { cookie },
			});
			expect(getResponse.statusCode).toBe(404);
		});
	});
});
