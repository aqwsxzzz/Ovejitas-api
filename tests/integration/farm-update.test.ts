import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser, createTestUser, getAuthCookie } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import { encodeId } from '../../src/utils/id-hash-util';
import { FarmMemberRole } from '../../src/resources/farm-member/farm-member.schema';

describe('Farm update & currencies', () => {
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

	describe('GET /api/v1/farms/currencies', () => {
		it('returns the list of supported currencies', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/farms/currencies',
				headers: { cookie },
			});
			expect(response.statusCode).toBe(200);
			const data = response.json().data;
			expect(Array.isArray(data)).toBe(true);
			const codes = data.map((c: { code: string }) => c.code);
			expect(codes).toContain('USD');
			expect(codes).toContain('EUR');
			expect(codes).toContain('ARS');
		});
	});

	describe('POST /api/v1/farms/:farmId (update)', () => {
		it('lets the owner update name, coords and currency', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const farmIdEncoded = encodeId(user.farmId);

			const response = await app.inject({
				method: 'POST',
				url: `/api/v1/farms/${farmIdEncoded}`,
				headers: { cookie },
				payload: {
					name: 'Updated Farm',
					latitude: -34.6,
					longitude: -58.4,
					currency: 'ARS',
				},
			});

			expect(response.statusCode).toBe(200);
			const farm = response.json().data;
			expect(farm.name).toBe('Updated Farm');
			expect(farm.latitude).toBe(-34.6);
			expect(farm.longitude).toBe(-58.4);
			expect(farm.currency).toBe('ARS');
		});

		it('returns 403 when a non-owner member tries to update', async () => {
			const owner = await createAuthenticatedUser(app);
			const farmIdEncoded = encodeId(owner.user.farmId);

			// Create a second user and attach them to the same farm as a plain member
			const member = await createTestUser(app);
			await app.db.models.FarmMember.create({
				farmId: owner.user.farmId,
				userId: member.id,
				role: FarmMemberRole.MEMBER,
			});
			// Point the member's lastVisitedFarmId at the shared farm so the auth plugin accepts them
			await app.db.models.User.update(
				{ lastVisitedFarmId: owner.user.farmId },
				{ where: { id: member.id } },
			);
			const memberCookie = getAuthCookie({ ...member, farmId: owner.user.farmId });

			const response = await app.inject({
				method: 'POST',
				url: `/api/v1/farms/${farmIdEncoded}`,
				headers: { cookie: memberCookie },
				payload: { currency: 'USD' },
			});

			expect(response.statusCode).toBe(403);
		});

		it('rejects an unsupported currency at the schema layer', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const farmIdEncoded = encodeId(user.farmId);

			const response = await app.inject({
				method: 'POST',
				url: `/api/v1/farms/${farmIdEncoded}`,
				headers: { cookie },
				payload: { currency: 'XYZ' },
			});

			expect(response.statusCode).toBe(400);
		});

		it('rejects out-of-range latitude', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const farmIdEncoded = encodeId(user.farmId);

			const response = await app.inject({
				method: 'POST',
				url: `/api/v1/farms/${farmIdEncoded}`,
				headers: { cookie },
				payload: { latitude: 999 },
			});

			expect(response.statusCode).toBe(400);
		});
	});
});
