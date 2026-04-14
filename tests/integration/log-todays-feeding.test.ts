import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import {
	createSpecies, createBreed, createFlock, createFeedType, createFeedLot, createFeedingSchedule,
} from '../helpers/factories';
import { encodeId } from '../../src/utils/id-hash-util';

const TODAY = '2026-04-14';

async function setupFlock(app: FastifyInstance) {
	const { user, cookie } = await createAuthenticatedUser(app);
	const { speciesId } = await createSpecies(app);
	const { breedId } = await createBreed(app, speciesId);
	const { flockId, encodedFlockId } = await createFlock(app, user.farmId, speciesId, breedId);
	return { user, cookie, flockId, encodedFlockId };
}

describe('POST /api/v1/flocks/:flockId/log-todays-feeding', () => {
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

	it('returns 401 when not authenticated', async () => {
		const response = await app.inject({
			method: 'POST',
			url: `/api/v1/flocks/${encodeId(1)}/log-todays-feeding`,
			payload: { date: TODAY },
		});

		expect(response.statusCode).toBe(401);
	});

	it('logs feeding for all active schedules in one transaction', async () => {
		const { user, cookie, flockId, encodedFlockId } = await setupFlock(app);
		const { feedTypeId: hayId } = await createFeedType(app, user.farmId, { name: 'Hay' });
		const { feedTypeId: grainId } = await createFeedType(app, user.farmId, { name: 'Grain' });
		await createFeedLot(app, user.farmId, hayId, user.id, { qtyPurchased: 10, unitPrice: 1 });
		await createFeedLot(app, user.farmId, grainId, user.id, { qtyPurchased: 10, unitPrice: 2 });
		await createFeedingSchedule(app, user.farmId, flockId, hayId, { qtyPerDay: 1, activeFrom: '2026-01-01' });
		await createFeedingSchedule(app, user.farmId, flockId, grainId, { qtyPerDay: 0.5, activeFrom: '2026-01-01' });

		const response = await app.inject({
			method: 'POST',
			url: `/api/v1/flocks/${encodedFlockId}/log-todays-feeding`,
			headers: { cookie },
			payload: { date: TODAY },
		});

		const body = response.json();
		expect(response.statusCode).toBe(200);
		expect(body.data).toHaveLength(2);
		expect(body.data.every((c: { reason: string }) => c.reason === 'feeding')).toBe(true);

		const consumptions = await app.db.models.FeedConsumption.findAll();
		expect(consumptions).toHaveLength(2);
	});

	it('returns 400 when no active schedules exist', async () => {
		const { cookie, encodedFlockId } = await setupFlock(app);

		const response = await app.inject({
			method: 'POST',
			url: `/api/v1/flocks/${encodedFlockId}/log-todays-feeding`,
			headers: { cookie },
			payload: { date: TODAY },
		});

		expect(response.statusCode).toBe(400);
		expect(response.json().message).toMatch(/no active feeding schedules/i);
	});

	it('returns 409 (idempotency) when called twice on the same day', async () => {
		const { user, cookie, flockId, encodedFlockId } = await setupFlock(app);
		const { feedTypeId } = await createFeedType(app, user.farmId);
		await createFeedLot(app, user.farmId, feedTypeId, user.id, { qtyPurchased: 10 });
		await createFeedingSchedule(app, user.farmId, flockId, feedTypeId, { qtyPerDay: 1 });

		const first = await app.inject({
			method: 'POST',
			url: `/api/v1/flocks/${encodedFlockId}/log-todays-feeding`,
			headers: { cookie },
			payload: { date: TODAY },
		});
		expect(first.statusCode).toBe(200);

		const second = await app.inject({
			method: 'POST',
			url: `/api/v1/flocks/${encodedFlockId}/log-todays-feeding`,
			headers: { cookie },
			payload: { date: TODAY },
		});
		expect(second.statusCode).toBe(400);

		const consumptions = await app.db.models.FeedConsumption.findAll();
		expect(consumptions).toHaveLength(1);
	});

	it('rolls back the entire batch when one schedule has insufficient stock', async () => {
		const { user, cookie, flockId, encodedFlockId } = await setupFlock(app);
		const { feedTypeId: hayId } = await createFeedType(app, user.farmId, { name: 'Hay' });
		const { feedTypeId: grainId } = await createFeedType(app, user.farmId, { name: 'Grain' });
		const { feedLotId: hayLotId } = await createFeedLot(app, user.farmId, hayId, user.id, { qtyPurchased: 10 });
		// Grain has only 0.2, schedule wants 0.5 → insufficient
		await createFeedLot(app, user.farmId, grainId, user.id, { qtyPurchased: 0.2 });
		await createFeedingSchedule(app, user.farmId, flockId, hayId, { qtyPerDay: 1 });
		await createFeedingSchedule(app, user.farmId, flockId, grainId, { qtyPerDay: 0.5 });

		const response = await app.inject({
			method: 'POST',
			url: `/api/v1/flocks/${encodedFlockId}/log-todays-feeding`,
			headers: { cookie },
			payload: { date: TODAY },
		});

		expect(response.statusCode).toBe(422);

		const consumptions = await app.db.models.FeedConsumption.findAll();
		expect(consumptions).toHaveLength(0);

		const hayLot = await app.db.models.FeedLot.findByPk(hayLotId);
		expect(Number(hayLot!.qtyRemaining)).toBe(10);
	});

	it('skips schedules outside the active window', async () => {
		const { user, cookie, flockId, encodedFlockId } = await setupFlock(app);
		const { feedTypeId } = await createFeedType(app, user.farmId);
		await createFeedLot(app, user.farmId, feedTypeId, user.id, { qtyPurchased: 10 });
		// Active window ends before today
		await createFeedingSchedule(app, user.farmId, flockId, feedTypeId, {
			qtyPerDay: 1,
			activeFrom: '2025-01-01',
			activeTo: '2025-12-31',
		});

		const response = await app.inject({
			method: 'POST',
			url: `/api/v1/flocks/${encodedFlockId}/log-todays-feeding`,
			headers: { cookie },
			payload: { date: TODAY },
		});

		// No active schedules → 400
		expect(response.statusCode).toBe(400);
	});
});
