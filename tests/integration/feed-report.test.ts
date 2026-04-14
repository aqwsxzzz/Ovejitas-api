import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import { createSpecies, createBreed, createFlock, createFeedType, createFeedLot } from '../helpers/factories';
import { encodeId } from '../../src/utils/id-hash-util';

async function seedScenario(app: FastifyInstance) {
	const { user, cookie } = await createAuthenticatedUser(app);
	const { speciesId } = await createSpecies(app);
	const { breedId } = await createBreed(app, speciesId);
	const { flockId: flockAId, encodedFlockId: flockAEncoded } = await createFlock(
		app, user.farmId, speciesId, breedId, { name: 'Flock A' },
	);
	const { flockId: flockBId, encodedFlockId: flockBEncoded } = await createFlock(
		app, user.farmId, speciesId, breedId, { name: 'Flock B' },
	);
	const { feedTypeId, encodedFeedTypeId } = await createFeedType(app, user.farmId, { name: 'Hay' });

	// Two lots: 10 units @ $1, then 5 units @ $2
	const { feedLotId: lot1Id, encodedFeedLotId: lot1Encoded } = await createFeedLot(
		app, user.farmId, feedTypeId, user.id, { qtyPurchased: 10, unitPrice: 1, purchasedAt: '2026-01-01' },
	);
	await createFeedLot(
		app, user.farmId, feedTypeId, user.id, { qtyPurchased: 5, unitPrice: 2, purchasedAt: '2026-02-01' },
	);

	return {
		user, cookie,
		flockAId, flockAEncoded,
		flockBId, flockBEncoded,
		feedTypeId, encodedFeedTypeId,
		lot1Id, lot1Encoded,
	};
}

async function recordConsumption(
	app: FastifyInstance,
	cookie: string,
	flockIdEncoded: string,
	feedTypeIdEncoded: string,
	qty: number,
	date: string,
) {
	return app.inject({
		method: 'POST',
		url: '/api/v1/feed-consumptions',
		headers: { cookie },
		payload: {
			flockId: flockIdEncoded,
			feedTypeId: feedTypeIdEncoded,
			qty,
			consumedAt: date,
			reason: 'feeding',
		},
	});
}

describe('Feed reports', () => {
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

	describe('GET /api/v1/feed-reports/cost-by-flock', () => {
		it('returns per-flock totals and feed-type breakdown with FIFO pricing', async () => {
			const { cookie, flockAEncoded, flockBEncoded, encodedFeedTypeId } = await seedScenario(app);

			// Flock A consumes 8 units (all from lot1 @ $1) → $8
			await recordConsumption(app, cookie, flockAEncoded, encodedFeedTypeId, 8, '2026-03-10');
			// Flock B consumes 4 units → 2 from lot1 @ $1 ($2) + 2 from lot2 @ $2 ($4) = $6
			await recordConsumption(app, cookie, flockBEncoded, encodedFeedTypeId, 4, '2026-03-11');

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/feed-reports/cost-by-flock',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.flocks).toHaveLength(2);

			const byId: Record<string, { totalQty: number; totalCost: number }> = {};
			for (const f of body.data.flocks) byId[f.flockId] = f;

			expect(byId[flockAEncoded]!.totalQty).toBe(8);
			expect(byId[flockAEncoded]!.totalCost).toBe(8);
			expect(byId[flockBEncoded]!.totalQty).toBe(4);
			expect(byId[flockBEncoded]!.totalCost).toBe(6);
		});

		it('filters by date range', async () => {
			const { cookie, flockAEncoded, encodedFeedTypeId } = await seedScenario(app);

			await recordConsumption(app, cookie, flockAEncoded, encodedFeedTypeId, 2, '2026-02-15');
			await recordConsumption(app, cookie, flockAEncoded, encodedFeedTypeId, 3, '2026-03-20');

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/feed-reports/cost-by-flock?from=2026-03-01&to=2026-03-31',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.flocks).toHaveLength(1);
			expect(body.data.flocks[0]!.totalQty).toBe(3);
		});

		it('filters to a single flock', async () => {
			const { cookie, flockAEncoded, flockBEncoded, encodedFeedTypeId } = await seedScenario(app);

			await recordConsumption(app, cookie, flockAEncoded, encodedFeedTypeId, 2, '2026-03-10');
			await recordConsumption(app, cookie, flockBEncoded, encodedFeedTypeId, 3, '2026-03-11');

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/feed-reports/cost-by-flock?flockId=${flockAEncoded}`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.flocks).toHaveLength(1);
			expect(body.data.flocks[0]!.flockId).toBe(flockAEncoded);
		});

		it('returns empty flocks array when no consumptions exist', async () => {
			const { cookie } = await seedScenario(app);

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/feed-reports/cost-by-flock',
				headers: { cookie },
			});

			expect(response.statusCode).toBe(200);
			expect(response.json().data.flocks).toEqual([]);
		});
	});

	describe('GET /api/v1/feed-reports/cost-by-lot/:lotId', () => {
		it('returns drawdowns per flock and totals for the lot', async () => {
			const { cookie, flockAEncoded, flockBEncoded, encodedFeedTypeId, lot1Encoded } = await seedScenario(app);

			// Both flocks draw only from lot1 (oldest)
			await recordConsumption(app, cookie, flockAEncoded, encodedFeedTypeId, 3, '2026-03-10');
			await recordConsumption(app, cookie, flockBEncoded, encodedFeedTypeId, 2, '2026-03-11');

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/feed-reports/cost-by-lot/${lot1Encoded}`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.qtyPurchased).toBe(10);
			expect(body.data.qtyRemaining).toBe(5);
			expect(body.data.qtyDrawn).toBe(5);
			expect(body.data.totalCost).toBe(5);
			expect(body.data.byFlock).toHaveLength(2);

			const byId: Record<string, { totalQty: number; totalCost: number }> = {};
			for (const f of body.data.byFlock) byId[f.flockId] = f;
			expect(byId[flockAEncoded]!.totalQty).toBe(3);
			expect(byId[flockAEncoded]!.totalCost).toBe(3);
			expect(byId[flockBEncoded]!.totalQty).toBe(2);
			expect(byId[flockBEncoded]!.totalCost).toBe(2);
		});

		it('returns 404 for an unknown lot', async () => {
			const { cookie } = await seedScenario(app);

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/feed-reports/cost-by-lot/${encodeId(99999)}`,
				headers: { cookie },
			});

			expect(response.statusCode).toBe(404);
		});
	});
});
