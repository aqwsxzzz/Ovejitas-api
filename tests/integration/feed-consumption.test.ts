import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import { createSpecies, createBreed, createFlock, createFeedType, createFeedLot } from '../helpers/factories';
import { encodeId } from '../../src/utils/id-hash-util';

async function setupFeedingScenario(app: FastifyInstance) {
	const { user, cookie } = await createAuthenticatedUser(app);
	const { speciesId } = await createSpecies(app);
	const { breedId } = await createBreed(app, speciesId);
	const { flockId, encodedFlockId } = await createFlock(app, user.farmId, speciesId, breedId);
	const { feedTypeId, encodedFeedTypeId } = await createFeedType(app, user.farmId);
	return { user, cookie, flockId, encodedFlockId, feedTypeId, encodedFeedTypeId };
}

describe('Feed consumption endpoints', () => {
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

	describe('POST /api/v1/feed-consumptions — FIFO drain', () => {
		it('drains the oldest lot first when capacity covers the request', async () => {
			const { user, cookie, encodedFlockId, feedTypeId, encodedFeedTypeId } = await setupFeedingScenario(app);
			const { feedLotId: lot1Id } = await createFeedLot(app, user.farmId, feedTypeId, user.id, {
				qtyPurchased: 10, unitPrice: 1, purchasedAt: '2026-01-01',
			});
			await createFeedLot(app, user.farmId, feedTypeId, user.id, {
				qtyPurchased: 5, unitPrice: 2, purchasedAt: '2026-02-01',
			});

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/feed-consumptions',
				headers: { cookie },
				payload: {
					flockId: encodedFlockId,
					feedTypeId: encodedFeedTypeId,
					qty: 8,
					consumedAt: '2026-02-15',
					reason: 'feeding',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.lots).toHaveLength(1);
			expect(body.data.lots[0].lotId).toBe(encodeId(lot1Id));
			expect(body.data.lots[0].qtyDrawn).toBe(8);
			expect(body.data.lots[0].unitPriceSnapshot).toBe(1);
			expect(body.data.totalCost).toBe(8);

			const reloadedLot1 = await app.db.models.FeedLot.findByPk(lot1Id);
			expect(Number(reloadedLot1!.qtyRemaining)).toBe(2);
		});

		it('spans multiple lots when one is not enough', async () => {
			const { user, cookie, encodedFlockId, feedTypeId, encodedFeedTypeId } = await setupFeedingScenario(app);
			const { feedLotId: lot1Id } = await createFeedLot(app, user.farmId, feedTypeId, user.id, {
				qtyPurchased: 3, unitPrice: 1, purchasedAt: '2026-01-01',
			});
			const { feedLotId: lot2Id } = await createFeedLot(app, user.farmId, feedTypeId, user.id, {
				qtyPurchased: 3, unitPrice: 2, purchasedAt: '2026-01-02',
			});
			const { feedLotId: lot3Id } = await createFeedLot(app, user.farmId, feedTypeId, user.id, {
				qtyPurchased: 3, unitPrice: 3, purchasedAt: '2026-01-03',
			});

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/feed-consumptions',
				headers: { cookie },
				payload: {
					flockId: encodedFlockId,
					feedTypeId: encodedFeedTypeId,
					qty: 7,
					consumedAt: '2026-01-10',
					reason: 'feeding',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.lots).toHaveLength(3);
			expect(body.data.totalCost).toBe(3 * 1 + 3 * 2 + 1 * 3);

			const lot3 = await app.db.models.FeedLot.findByPk(lot3Id);
			expect(Number(lot3!.qtyRemaining)).toBe(2);

			const lot1 = await app.db.models.FeedLot.findByPk(lot1Id);
			expect(Number(lot1!.qtyRemaining)).toBe(0);
			const lot2 = await app.db.models.FeedLot.findByPk(lot2Id);
			expect(Number(lot2!.qtyRemaining)).toBe(0);
		});

		it('rejects with 422 when total stock is less than requested', async () => {
			const { user, cookie, encodedFlockId, feedTypeId, encodedFeedTypeId } = await setupFeedingScenario(app);
			const { feedLotId } = await createFeedLot(app, user.farmId, feedTypeId, user.id, {
				qtyPurchased: 5, unitPrice: 1,
			});

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/feed-consumptions',
				headers: { cookie },
				payload: {
					flockId: encodedFlockId,
					feedTypeId: encodedFeedTypeId,
					qty: 6,
					consumedAt: '2026-02-01',
					reason: 'feeding',
				},
			});

			expect(response.statusCode).toBe(422);

			const consumptions = await app.db.models.FeedConsumption.findAll();
			expect(consumptions).toHaveLength(0);
			const consumptionLots = await app.db.models.FeedConsumptionLot.findAll();
			expect(consumptionLots).toHaveLength(0);

			const lot = await app.db.models.FeedLot.findByPk(feedLotId);
			expect(Number(lot!.qtyRemaining)).toBe(5);
		});

		it('rejects with 422 when no lots exist at all', async () => {
			const { cookie, encodedFlockId, encodedFeedTypeId } = await setupFeedingScenario(app);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/feed-consumptions',
				headers: { cookie },
				payload: {
					flockId: encodedFlockId,
					feedTypeId: encodedFeedTypeId,
					qty: 1,
					consumedAt: '2026-02-01',
					reason: 'feeding',
				},
			});

			expect(response.statusCode).toBe(422);
		});

		it('does not retroactively rewrite past consumptions when a lot is backdated', async () => {
			const { user, cookie, encodedFlockId, feedTypeId, encodedFeedTypeId } = await setupFeedingScenario(app);
			const { feedLotId: lotAId } = await createFeedLot(app, user.farmId, feedTypeId, user.id, {
				qtyPurchased: 10, unitPrice: 5, purchasedAt: '2026-03-01',
			});

			const firstResponse = await app.inject({
				method: 'POST',
				url: '/api/v1/feed-consumptions',
				headers: { cookie },
				payload: {
					flockId: encodedFlockId, feedTypeId: encodedFeedTypeId,
					qty: 4, consumedAt: '2026-03-10', reason: 'feeding',
				},
			});
			const firstBody = firstResponse.json();
			expect(firstBody.data.lots[0].lotId).toBe(encodeId(lotAId));
			expect(firstBody.data.lots[0].unitPriceSnapshot).toBe(5);

			const { feedLotId: lotBId } = await createFeedLot(app, user.farmId, feedTypeId, user.id, {
				qtyPurchased: 10, unitPrice: 1, purchasedAt: '2026-02-01',
			});

			const oldConsumptionLots = await app.db.models.FeedConsumptionLot.findAll();
			expect(oldConsumptionLots).toHaveLength(1);
			expect(oldConsumptionLots[0].lotId).toBe(lotAId);
			expect(Number(oldConsumptionLots[0].unitPriceSnapshot)).toBe(5);

			const secondResponse = await app.inject({
				method: 'POST',
				url: '/api/v1/feed-consumptions',
				headers: { cookie },
				payload: {
					flockId: encodedFlockId, feedTypeId: encodedFeedTypeId,
					qty: 3, consumedAt: '2026-03-15', reason: 'feeding',
				},
			});
			const secondBody = secondResponse.json();
			expect(secondBody.data.lots[0].lotId).toBe(encodeId(lotBId));
			expect(secondBody.data.lots[0].unitPriceSnapshot).toBe(1);
		});

		it('rejects feeding consumption without a flock', async () => {
			const { cookie, encodedFeedTypeId } = await setupFeedingScenario(app);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/feed-consumptions',
				headers: { cookie },
				payload: {
					feedTypeId: encodedFeedTypeId,
					qty: 1,
					consumedAt: '2026-02-01',
					reason: 'feeding',
				},
			});

			expect(response.statusCode).toBe(400);
		});

		it('allows waste consumption without a flock', async () => {
			const { user, cookie, feedTypeId, encodedFeedTypeId } = await setupFeedingScenario(app);
			await createFeedLot(app, user.farmId, feedTypeId, user.id, { qtyPurchased: 5 });

			const response = await app.inject({
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

			expect(response.statusCode).toBe(200);
			expect(response.json().data.flockId).toBeNull();
		});
	});

	describe('DELETE /api/v1/feed-consumptions/:id', () => {
		it('reverses the drain and restores lot qtyRemaining', async () => {
			const { user, cookie, encodedFlockId, feedTypeId, encodedFeedTypeId } = await setupFeedingScenario(app);
			const { feedLotId } = await createFeedLot(app, user.farmId, feedTypeId, user.id, {
				qtyPurchased: 10, unitPrice: 1,
			});

			const createResponse = await app.inject({
				method: 'POST',
				url: '/api/v1/feed-consumptions',
				headers: { cookie },
				payload: {
					flockId: encodedFlockId, feedTypeId: encodedFeedTypeId,
					qty: 5, consumedAt: '2026-02-01', reason: 'feeding',
				},
			});
			const consumptionId = createResponse.json().data.id;

			const lotAfterCreate = await app.db.models.FeedLot.findByPk(feedLotId);
			expect(Number(lotAfterCreate!.qtyRemaining)).toBe(5);

			const deleteResponse = await app.inject({
				method: 'DELETE',
				url: `/api/v1/feed-consumptions/${consumptionId}`,
				headers: { cookie },
			});

			expect(deleteResponse.statusCode).toBe(200);

			const lotAfterDelete = await app.db.models.FeedLot.findByPk(feedLotId);
			expect(Number(lotAfterDelete!.qtyRemaining)).toBe(10);

			const remainingLinks = await app.db.models.FeedConsumptionLot.findAll();
			expect(remainingLinks).toHaveLength(0);
		});
	});

	describe('GET /api/v1/feed-consumptions', () => {
		it('lists consumptions with lots when include=lots', async () => {
			const { user, cookie, encodedFlockId, feedTypeId, encodedFeedTypeId } = await setupFeedingScenario(app);
			await createFeedLot(app, user.farmId, feedTypeId, user.id, { qtyPurchased: 10 });

			await app.inject({
				method: 'POST',
				url: '/api/v1/feed-consumptions',
				headers: { cookie },
				payload: {
					flockId: encodedFlockId, feedTypeId: encodedFeedTypeId,
					qty: 2, consumedAt: '2026-02-01', reason: 'feeding',
				},
			});

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/feed-consumptions?include=lots',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(1);
			expect(body.data[0].lots).toHaveLength(1);
		});
	});
});
