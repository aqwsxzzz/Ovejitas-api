import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import { createSpecies, createBreed, createFlock } from '../helpers/factories';

describe('Egg collection — multiple per day', () => {
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

	it('allows two collections on the same date for the same flock', async () => {
		const { user, cookie } = await createAuthenticatedUser(app);
		const { speciesId } = await createSpecies(app, { name: 'Layer' });
		const { breedId } = await createBreed(app, speciesId);
		const { encodedFlockId } = await createFlock(app, user.farmId, speciesId, breedId, { name: 'Morning Flock' });

		const first = await app.inject({
			method: 'POST',
			url: `/api/v1/flocks/${encodedFlockId}/egg-collections`,
			headers: { cookie },
			payload: { date: '2026-04-18', totalEggs: 12, brokenEggs: 0 },
		});
		const second = await app.inject({
			method: 'POST',
			url: `/api/v1/flocks/${encodedFlockId}/egg-collections`,
			headers: { cookie },
			payload: { date: '2026-04-18', totalEggs: 8, brokenEggs: 1 },
		});

		expect(first.statusCode).toBe(200);
		expect(second.statusCode).toBe(200);

		const list = await app.inject({
			method: 'GET',
			url: `/api/v1/flocks/${encodedFlockId}/egg-collections`,
			headers: { cookie },
		});
		expect(list.statusCode).toBe(200);
		expect(list.json().data).toHaveLength(2);
	});
});
