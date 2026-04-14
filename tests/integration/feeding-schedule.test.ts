import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import { createSpecies, createBreed, createFlock, createFeedType, createFeedingSchedule } from '../helpers/factories';
import { encodeId } from '../../src/utils/id-hash-util';

async function setupFlockAndFeedType(app: FastifyInstance) {
	const { user, cookie } = await createAuthenticatedUser(app);
	const { speciesId } = await createSpecies(app);
	const { breedId } = await createBreed(app, speciesId);
	const { flockId, encodedFlockId } = await createFlock(app, user.farmId, speciesId, breedId);
	const { feedTypeId, encodedFeedTypeId } = await createFeedType(app, user.farmId);
	return { user, cookie, flockId, encodedFlockId, feedTypeId, encodedFeedTypeId };
}

describe('Feeding schedule endpoints', () => {
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

	describe('POST /api/v1/feeding-schedules', () => {
		it('creates a schedule', async () => {
			const { cookie, encodedFlockId, encodedFeedTypeId } = await setupFlockAndFeedType(app);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/feeding-schedules',
				headers: { cookie },
				payload: {
					flockId: encodedFlockId,
					feedTypeId: encodedFeedTypeId,
					qtyPerDay: 1.5,
					activeFrom: '2026-01-01',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.qtyPerDay).toBe(1.5);
			expect(body.data.activeFrom).toBe('2026-01-01');
			expect(body.data.activeTo).toBeNull();
		});

		it('returns 400 for unknown flock', async () => {
			const { cookie, encodedFeedTypeId } = await setupFlockAndFeedType(app);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/feeding-schedules',
				headers: { cookie },
				payload: {
					flockId: encodeId(99999),
					feedTypeId: encodedFeedTypeId,
					qtyPerDay: 1,
					activeFrom: '2026-01-01',
				},
			});

			expect(response.statusCode).toBe(400);
		});

		it('rejects a second open-ended schedule for the same (flock, feed_type)', async () => {
			const { user, cookie, flockId, feedTypeId, encodedFlockId, encodedFeedTypeId } = await setupFlockAndFeedType(app);
			await createFeedingSchedule(app, user.farmId, flockId, feedTypeId, { activeTo: null });

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/feeding-schedules',
				headers: { cookie },
				payload: {
					flockId: encodedFlockId,
					feedTypeId: encodedFeedTypeId,
					qtyPerDay: 2,
					activeFrom: '2026-02-01',
				},
			});

			expect(response.statusCode).toBe(400);
		});

		it('allows a closed schedule then a new open-ended one', async () => {
			const { user, cookie, flockId, feedTypeId, encodedFlockId, encodedFeedTypeId } = await setupFlockAndFeedType(app);
			await createFeedingSchedule(app, user.farmId, flockId, feedTypeId, {
				activeFrom: '2025-01-01',
				activeTo: '2025-12-31',
			});

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/feeding-schedules',
				headers: { cookie },
				payload: {
					flockId: encodedFlockId,
					feedTypeId: encodedFeedTypeId,
					qtyPerDay: 2,
					activeFrom: '2026-01-01',
				},
			});

			expect(response.statusCode).toBe(200);
		});
	});

	describe('GET /api/v1/feeding-schedules', () => {
		it('lists schedules filtered by flock', async () => {
			const { user, cookie, flockId, feedTypeId } = await setupFlockAndFeedType(app);
			await createFeedingSchedule(app, user.farmId, flockId, feedTypeId);

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/feeding-schedules?flockId=${encodeId(flockId)}`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(1);
		});
	});

	describe('PUT /api/v1/feeding-schedules/:id', () => {
		it('updates qty and active range', async () => {
			const { user, cookie, flockId, feedTypeId } = await setupFlockAndFeedType(app);
			const { encodedScheduleId } = await createFeedingSchedule(app, user.farmId, flockId, feedTypeId);

			const response = await app.inject({
				method: 'PUT',
				url: `/api/v1/feeding-schedules/${encodedScheduleId}`,
				headers: { cookie },
				payload: { qtyPerDay: 2.5, activeTo: '2026-12-31' },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.qtyPerDay).toBe(2.5);
			expect(body.data.activeTo).toBe('2026-12-31');
		});
	});

	describe('DELETE /api/v1/feeding-schedules/:id', () => {
		it('deletes a schedule', async () => {
			const { user, cookie, flockId, feedTypeId } = await setupFlockAndFeedType(app);
			const { encodedScheduleId } = await createFeedingSchedule(app, user.farmId, flockId, feedTypeId);

			const response = await app.inject({
				method: 'DELETE',
				url: `/api/v1/feeding-schedules/${encodedScheduleId}`,
				headers: { cookie },
			});

			expect(response.statusCode).toBe(200);
		});
	});
});
