import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import { createFeedType, createFeedLot } from '../helpers/factories';
import { encodeId } from '../../src/utils/id-hash-util';

describe('Feed lot endpoints', () => {
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

	describe('POST /api/v1/feed-lots', () => {
		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/feed-lots',
				payload: { feedTypeId: 'fake', qtyPurchased: 10, unitPrice: 2, purchasedAt: '2026-01-01' },
			});

			expect(response.statusCode).toBe(401);
		});

		it('creates a feed lot with qtyRemaining equal to qtyPurchased', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { encodedFeedTypeId } = await createFeedType(app, user.farmId, { name: 'Hay' });

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/feed-lots',
				headers: { cookie },
				payload: {
					feedTypeId: encodedFeedTypeId,
					qtyPurchased: 25,
					unitPrice: 1.5,
					purchasedAt: '2026-01-15',
					supplier: 'Supplier A',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.qtyPurchased).toBe(25);
			expect(body.data.qtyRemaining).toBe(25);
			expect(body.data.unitPrice).toBe(1.5);
			expect(body.data.supplier).toBe('Supplier A');
		});

		it('rejects creation when feed type does not exist on this farm', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/feed-lots',
				headers: { cookie },
				payload: {
					feedTypeId: encodeId(99999),
					qtyPurchased: 10,
					unitPrice: 1,
					purchasedAt: '2026-01-01',
				},
			});

			expect(response.statusCode).toBe(400);
		});
	});

	describe('PUT /api/v1/feed-lots/:id', () => {
		it('allows price edit on an untouched lot', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { feedTypeId } = await createFeedType(app, user.farmId);
			const { encodedFeedLotId } = await createFeedLot(app, user.farmId, feedTypeId, user.id, {
				qtyPurchased: 10,
				unitPrice: 1,
			});

			const response = await app.inject({
				method: 'PUT',
				url: `/api/v1/feed-lots/${encodedFeedLotId}`,
				headers: { cookie },
				payload: { unitPrice: 2 },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.unitPrice).toBe(2);
		});

		it('returns 422 when editing price on a partially consumed lot', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { feedTypeId, encodedFeedTypeId } = await createFeedType(app, user.farmId);
			const { encodedFeedLotId } = await createFeedLot(app, user.farmId, feedTypeId, user.id, {
				qtyPurchased: 10,
				unitPrice: 1,
			});

			await app.inject({
				method: 'POST',
				url: '/api/v1/feed-consumptions',
				headers: { cookie },
				payload: {
					feedTypeId: encodedFeedTypeId,
					qty: 1,
					consumedAt: '2026-02-01',
					reason: 'waste',
				},
			});

			const response = await app.inject({
				method: 'PUT',
				url: `/api/v1/feed-lots/${encodedFeedLotId}`,
				headers: { cookie },
				payload: { unitPrice: 5 },
			});

			expect(response.statusCode).toBe(422);
			expect(response.json().message).toMatch(/cannot edit price/i);
		});

		it('allows non-price edits (notes) on partially consumed lot', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { feedTypeId, encodedFeedTypeId } = await createFeedType(app, user.farmId);
			const { encodedFeedLotId } = await createFeedLot(app, user.farmId, feedTypeId, user.id, {
				qtyPurchased: 10,
				unitPrice: 1,
			});

			await app.inject({
				method: 'POST',
				url: '/api/v1/feed-consumptions',
				headers: { cookie },
				payload: {
					feedTypeId: encodedFeedTypeId,
					qty: 1,
					consumedAt: '2026-02-01',
					reason: 'waste',
				},
			});

			const response = await app.inject({
				method: 'PUT',
				url: `/api/v1/feed-lots/${encodedFeedLotId}`,
				headers: { cookie },
				payload: { notes: 'Updated notes' },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.notes).toBe('Updated notes');
		});
	});

	describe('DELETE /api/v1/feed-lots/:id', () => {
		it('deletes an unused lot', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { feedTypeId } = await createFeedType(app, user.farmId);
			const { encodedFeedLotId } = await createFeedLot(app, user.farmId, feedTypeId, user.id);

			const response = await app.inject({
				method: 'DELETE',
				url: `/api/v1/feed-lots/${encodedFeedLotId}`,
				headers: { cookie },
			});

			expect(response.statusCode).toBe(200);
		});

		it('returns 409 when the lot has consumption history', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { feedTypeId, encodedFeedTypeId } = await createFeedType(app, user.farmId);
			const { encodedFeedLotId } = await createFeedLot(app, user.farmId, feedTypeId, user.id, {
				qtyPurchased: 10,
			});

			await app.inject({
				method: 'POST',
				url: '/api/v1/feed-consumptions',
				headers: { cookie },
				payload: {
					feedTypeId: encodedFeedTypeId,
					qty: 1,
					consumedAt: '2026-02-01',
					reason: 'waste',
				},
			});

			const response = await app.inject({
				method: 'DELETE',
				url: `/api/v1/feed-lots/${encodedFeedLotId}`,
				headers: { cookie },
			});

			expect(response.statusCode).toBe(409);
		});
	});

	describe('GET /api/v1/feed-lots', () => {
		it('lists lots scoped to the current farm', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { feedTypeId } = await createFeedType(app, user.farmId);
			await createFeedLot(app, user.farmId, feedTypeId, user.id, { purchasedAt: '2026-01-01' });
			await createFeedLot(app, user.farmId, feedTypeId, user.id, { purchasedAt: '2026-02-01' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/feed-lots',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(2);
			expect(body.meta.pagination.total).toBe(2);
		});
	});
});
