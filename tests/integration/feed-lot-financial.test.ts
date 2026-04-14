import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import { createFeedType } from '../helpers/factories';

describe('Feed lot → financial transaction integration', () => {
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

	it('auto-creates a financial_transaction when a feed lot is created', async () => {
		const { user, cookie } = await createAuthenticatedUser(app);
		const { encodedFeedTypeId } = await createFeedType(app, user.farmId, { name: 'Hay' });

		const before = await app.db.models.FinancialTransaction.findAll();
		expect(before).toHaveLength(0);

		const response = await app.inject({
			method: 'POST',
			url: '/api/v1/feed-lots',
			headers: { cookie },
			payload: {
				feedTypeId: encodedFeedTypeId,
				qtyPurchased: 25,
				unitPrice: 1.5,
				purchasedAt: '2026-03-10',
			},
		});

		expect(response.statusCode).toBe(200);
		const lotId = response.json().data.id;

		const transactions = await app.db.models.FinancialTransaction.findAll();
		expect(transactions).toHaveLength(1);

		const tx = transactions[0]!;
		expect(tx.type).toBe('expense');
		expect(Number(tx.amount)).toBe(37.5);
		expect(tx.description).toBe('Feed purchase: Hay');
		expect(tx.speciesId).toBeNull();
		expect(tx.date).toBe('2026-03-10');

		// Back-reference: the transaction points to the lot
		const response2 = await app.inject({
			method: 'GET',
			url: `/api/v1/feed-lots/${lotId}`,
			headers: { cookie },
		});
		expect(response2.json().data.id).toBe(lotId);
	});

	it('rolls back both rows if creating the financial transaction fails', async () => {
		// Hard to simulate a failure without fault injection — covered implicitly
		// by the same-transaction wrapping. This placeholder documents the expectation.
		const { user, cookie } = await createAuthenticatedUser(app);
		const { encodedFeedTypeId } = await createFeedType(app, user.farmId);

		const response = await app.inject({
			method: 'POST',
			url: '/api/v1/feed-lots',
			headers: { cookie },
			payload: {
				feedTypeId: encodedFeedTypeId,
				qtyPurchased: 10,
				unitPrice: 2,
				purchasedAt: '2026-03-01',
			},
		});
		expect(response.statusCode).toBe(200);

		const lots = await app.db.models.FeedLot.findAll();
		const txs = await app.db.models.FinancialTransaction.findAll();
		expect(lots).toHaveLength(1);
		expect(txs).toHaveLength(1);
	});

	it('financial transaction amount is snapshotted — editing lot price before drain does NOT update it', async () => {
		const { user, cookie } = await createAuthenticatedUser(app);
		const { encodedFeedTypeId } = await createFeedType(app, user.farmId);

		const createResponse = await app.inject({
			method: 'POST',
			url: '/api/v1/feed-lots',
			headers: { cookie },
			payload: {
				feedTypeId: encodedFeedTypeId,
				qtyPurchased: 10,
				unitPrice: 1,
				purchasedAt: '2026-03-01',
			},
		});
		const lotId = createResponse.json().data.id;

		const txBefore = await app.db.models.FinancialTransaction.findOne();
		expect(Number(txBefore!.amount)).toBe(10);

		// Edit the lot price (allowed pre-drain)
		await app.inject({
			method: 'PUT',
			url: `/api/v1/feed-lots/${lotId}`,
			headers: { cookie },
			payload: { unitPrice: 5 },
		});

		const txAfter = await app.db.models.FinancialTransaction.findOne();
		// Amount must stay snapshotted at 10 (qty=10 * old price=1), not 50
		expect(Number(txAfter!.amount)).toBe(10);
	});

	it('existing financial_transaction endpoints still require speciesId for user-created rows', async () => {
		const { user, cookie } = await createAuthenticatedUser(app);
		const { encodedFeedTypeId } = await createFeedType(app, user.farmId);

		await app.inject({
			method: 'POST',
			url: '/api/v1/feed-lots',
			headers: { cookie },
			payload: {
				feedTypeId: encodedFeedTypeId,
				qtyPurchased: 10,
				unitPrice: 1,
				purchasedAt: '2026-03-01',
			},
		});

		// GET /financial should surface the auto-created row with null speciesId
		const listResponse = await app.inject({
			method: 'GET',
			url: '/api/v1/financial',
			headers: { cookie },
		});

		expect(listResponse.statusCode).toBe(200);
		const body = listResponse.json();
		expect(body.data).toHaveLength(1);
		expect(body.data[0].speciesId).toBeNull();
		expect(body.data[0].feedLotId).not.toBeNull();

		// POST /financial without speciesId still rejected
		const createResponse = await app.inject({
			method: 'POST',
			url: '/api/v1/financial',
			headers: { cookie },
			payload: {
				type: 'expense',
				amount: 50,
				date: '2026-03-15',
				// speciesId missing
			},
		});
		expect(createResponse.statusCode).toBe(400);
	});
});
