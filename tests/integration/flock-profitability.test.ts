import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import { createSpecies, createBreed, createFlock, createFeedType, createFeedLot } from '../helpers/factories';

interface Ctx {
	cookie: string;
	farmId: number;
	userId: number;
	flockAId: number;
	flockAEncoded: string;
	flockBId: number;
	flockBEncoded: string;
	feedTypeId: number;
	feedTypeEncoded: string;
}

async function seed(app: FastifyInstance): Promise<Ctx> {
	const { user, cookie } = await createAuthenticatedUser(app);
	const { speciesId } = await createSpecies(app, { name: 'Chicken' });
	const { breedId } = await createBreed(app, speciesId);
	const { flockId: flockAId, encodedFlockId: flockAEncoded } = await createFlock(
		app, user.farmId, speciesId, breedId, { name: 'Flock A' },
	);
	const { flockId: flockBId, encodedFlockId: flockBEncoded } = await createFlock(
		app, user.farmId, speciesId, breedId, { name: 'Flock B' },
	);
	const { feedTypeId, encodedFeedTypeId } = await createFeedType(app, user.farmId, { name: 'Layer Feed' });
	await createFeedLot(app, user.farmId, feedTypeId, user.id, {
		qtyPurchased: 1000, unitPrice: 0.5, purchasedAt: '2026-01-01',
	});

	return {
		cookie,
		farmId: user.farmId,
		userId: user.id,
		flockAId,
		flockAEncoded,
		flockBId,
		flockBEncoded,
		feedTypeId,
		feedTypeEncoded: encodedFeedTypeId,
	};
}

async function setActivePrice(app: FastifyInstance, cookie: string, pricePerEgg: number, effectiveFrom: string) {
	return app.inject({
		method: 'POST',
		url: '/api/v1/egg-pricings',
		headers: { cookie },
		payload: { pricePerEgg, effectiveFrom },
	});
}

async function logEggs(
	app: FastifyInstance,
	flockId: number,
	date: string,
	totalEggs: number,
	brokenEggs = 0,
) {
	await app.db.models.EggCollection.create({ flockId, date, totalEggs, brokenEggs });
}

async function logConsumption(
	app: FastifyInstance,
	cookie: string,
	flockEncoded: string,
	feedTypeEncoded: string,
	qty: number,
	date: string,
) {
	return app.inject({
		method: 'POST',
		url: '/api/v1/feed-consumptions',
		headers: { cookie },
		payload: {
			flockId: flockEncoded,
			feedTypeId: feedTypeEncoded,
			qty,
			consumedAt: date,
			reason: 'feeding',
		},
	});
}

describe('Flock profitability report', () => {
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

	it('returns 409 when no egg pricing is configured', async () => {
		const ctx = await seed(app);

		const response = await app.inject({
			method: 'GET',
			url: '/api/v1/reports/flock-profitability?period=monthly&from=2026-01-01&to=2026-01-31',
			headers: { cookie: ctx.cookie },
		});

		expect(response.statusCode).toBe(409);
	});

	it('computes revenue from sellable eggs (excluding broken) with single active price', async () => {
		const ctx = await seed(app);
		await setActivePrice(app, ctx.cookie, 0.5, '2026-01-01');

		await logEggs(app, ctx.flockAId, '2026-01-10', 30, 0);
		await logEggs(app, ctx.flockAId, '2026-01-11', 30, 6); // 24 sellable
		await logConsumption(app, ctx.cookie, ctx.flockAEncoded, ctx.feedTypeEncoded, 10, '2026-01-10');

		const response = await app.inject({
			method: 'GET',
			url: '/api/v1/reports/flock-profitability?period=monthly&from=2026-01-01&to=2026-01-31',
			headers: { cookie: ctx.cookie },
		});

		expect(response.statusCode).toBe(200);
		const body = response.json().data;
		expect(body.flocks).toHaveLength(1);

		const row = body.flocks[0];
		expect(row.flockId).toBe(ctx.flockAEncoded);
		expect(row.eggsCollected).toBe(60);
		expect(row.brokenEggs).toBe(6);
		expect(row.eggsSellable).toBe(54);
		expect(row.totalEggRevenue).toBe(27);
		expect(row.totalFeedCost).toBe(5);
		expect(row.profit).toBe(22);
		expect(row.periodBreakdown).toHaveLength(1);
		expect(row.periodBreakdown[0].period).toBe('2026-01');
	});

	it('applies historical pricing — collections use the price active on their date', async () => {
		const ctx = await seed(app);
		await setActivePrice(app, ctx.cookie, 0.5, '2026-01-01');
		await setActivePrice(app, ctx.cookie, 1.0, '2026-02-01');

		await logEggs(app, ctx.flockAId, '2026-01-15', 10, 0); // 10 × 0.5 = 5
		await logEggs(app, ctx.flockAId, '2026-02-15', 10, 0); // 10 × 1.0 = 10

		const response = await app.inject({
			method: 'GET',
			url: '/api/v1/reports/flock-profitability?period=monthly&from=2026-01-01&to=2026-02-28',
			headers: { cookie: ctx.cookie },
		});

		expect(response.statusCode).toBe(200);
		const row = response.json().data.flocks[0];
		expect(row.totalEggRevenue).toBe(15);
		expect(row.periodBreakdown).toHaveLength(2);
		const jan = row.periodBreakdown.find((p: { period: string }) => p.period === '2026-01');
		const feb = row.periodBreakdown.find((p: { period: string }) => p.period === '2026-02');
		expect(jan.eggRevenue).toBe(5);
		expect(feb.eggRevenue).toBe(10);
	});

	it('includes flocks with only feed cost (negative profit, no revenue)', async () => {
		const ctx = await seed(app);
		await setActivePrice(app, ctx.cookie, 0.5, '2026-01-01');

		await logEggs(app, ctx.flockAId, '2026-01-10', 30);
		await logConsumption(app, ctx.cookie, ctx.flockAEncoded, ctx.feedTypeEncoded, 5, '2026-01-10');
		await logConsumption(app, ctx.cookie, ctx.flockBEncoded, ctx.feedTypeEncoded, 8, '2026-01-10');

		const response = await app.inject({
			method: 'GET',
			url: '/api/v1/reports/flock-profitability?period=monthly&from=2026-01-01&to=2026-01-31',
			headers: { cookie: ctx.cookie },
		});

		const flocks = response.json().data.flocks;
		expect(flocks).toHaveLength(2);
		const b = flocks.find((f: { flockId: string }) => f.flockId === ctx.flockBEncoded);
		expect(b.eggsCollected).toBe(0);
		expect(b.totalEggRevenue).toBe(0);
		expect(b.totalFeedCost).toBe(4);
		expect(b.profit).toBe(-4);
		expect(b.profitMargin).toBeNull();
	});

	it('supports filtering to a single flock via flockId', async () => {
		const ctx = await seed(app);
		await setActivePrice(app, ctx.cookie, 0.5, '2026-01-01');
		await logEggs(app, ctx.flockAId, '2026-01-10', 30);
		await logEggs(app, ctx.flockBId, '2026-01-10', 30);

		const response = await app.inject({
			method: 'GET',
			url: `/api/v1/reports/flock-profitability?period=monthly&from=2026-01-01&to=2026-01-31&flockId=${ctx.flockAEncoded}`,
			headers: { cookie: ctx.cookie },
		});

		const flocks = response.json().data.flocks;
		expect(flocks).toHaveLength(1);
		expect(flocks[0].flockId).toBe(ctx.flockAEncoded);
	});

	it('warns when a collection has no active price on its date', async () => {
		const ctx = await seed(app);
		await setActivePrice(app, ctx.cookie, 0.5, '2026-02-01');
		await logEggs(app, ctx.flockAId, '2026-01-10', 30); // before any active price

		const response = await app.inject({
			method: 'GET',
			url: '/api/v1/reports/flock-profitability?period=monthly&from=2026-01-01&to=2026-02-28',
			headers: { cookie: ctx.cookie },
		});

		const row = response.json().data.flocks[0];
		expect(row.totalEggRevenue).toBe(0);
		expect(row.warnings.length).toBeGreaterThan(0);
	});

	it('rejects an invalid date range', async () => {
		const ctx = await seed(app);
		await setActivePrice(app, ctx.cookie, 0.5, '2026-01-01');

		const response = await app.inject({
			method: 'GET',
			url: '/api/v1/reports/flock-profitability?period=daily&from=2026-02-01&to=2026-01-01',
			headers: { cookie: ctx.cookie },
		});

		expect(response.statusCode).toBe(400);
	});
});
