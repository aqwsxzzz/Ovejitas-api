import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';

describe('Egg pricing', () => {
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

	async function setPrice(cookie: string, pricePerEgg: number, effectiveFrom: string) {
		return app.inject({
			method: 'POST',
			url: '/api/v1/egg-pricings',
			headers: { cookie },
			payload: { pricePerEgg, effectiveFrom },
		});
	}

	it('returns 404 when no pricing is configured', async () => {
		const { cookie } = await createAuthenticatedUser(app);
		const response = await app.inject({
			method: 'GET',
			url: '/api/v1/egg-pricings/active',
			headers: { cookie },
		});
		expect(response.statusCode).toBe(404);
	});

	it('creates an open pricing row and returns it as the active price', async () => {
		const { cookie } = await createAuthenticatedUser(app);
		const create = await setPrice(cookie, 0.5, '2026-01-01');
		expect(create.statusCode).toBe(201);
		expect(create.json().data.pricePerEgg).toBe(0.5);
		expect(create.json().data.effectiveTo).toBeNull();

		const active = await app.inject({
			method: 'GET',
			url: '/api/v1/egg-pricings/active',
			headers: { cookie },
		});
		expect(active.statusCode).toBe(200);
		expect(active.json().data.pricePerEgg).toBe(0.5);
	});

	it('closes the prior open row when a new price is set', async () => {
		const { cookie } = await createAuthenticatedUser(app);
		await setPrice(cookie, 0.5, '2026-01-01');
		const second = await setPrice(cookie, 0.6, '2026-02-01');
		expect(second.statusCode).toBe(201);

		const history = await app.inject({
			method: 'GET',
			url: '/api/v1/egg-pricings/history',
			headers: { cookie },
		});
		const rows = history.json().data;
		expect(rows).toHaveLength(2);

		const newest = rows.find((r: { pricePerEgg: number }) => r.pricePerEgg === 0.6);
		const oldest = rows.find((r: { pricePerEgg: number }) => r.pricePerEgg === 0.5);
		expect(newest.effectiveFrom).toBe('2026-02-01');
		expect(newest.effectiveTo).toBeNull();
		expect(oldest.effectiveFrom).toBe('2026-01-01');
		expect(oldest.effectiveTo).toBe('2026-01-31');
	});

	it('rejects a new price that is not strictly after the current one', async () => {
		const { cookie } = await createAuthenticatedUser(app);
		await setPrice(cookie, 0.5, '2026-02-01');
		const conflict = await setPrice(cookie, 0.6, '2026-02-01');
		expect(conflict.statusCode).toBe(409);
	});

	it('isolates pricing per farm', async () => {
		const farmA = await createAuthenticatedUser(app);
		const farmB = await createAuthenticatedUser(app);

		await setPrice(farmA.cookie, 0.5, '2026-01-01');

		const bActive = await app.inject({
			method: 'GET',
			url: '/api/v1/egg-pricings/active',
			headers: { cookie: farmB.cookie },
		});
		expect(bActive.statusCode).toBe(404);
	});
});
