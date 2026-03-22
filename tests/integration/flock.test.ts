import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import { createSpecies, createBreed, createFlock } from '../helpers/factories';
import { encodeId } from '../../src/utils/id-hash-util';

describe('Flock endpoints', () => {
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

	describe('GET /api/v1/flocks', () => {
		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/flocks?language=en',
			});

			expect(response.statusCode).toBe(401);
		});

		it('returns flocks with default pagination', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createFlock(app, user.farmId, speciesId, breedId, { name: 'Flock A' });
			await createFlock(app, user.farmId, speciesId, breedId, { name: 'Flock B' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/flocks?language=en',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data).toHaveLength(2);
			expect(body.meta.pagination).toBeDefined();
			expect(body.meta.pagination.total).toBe(2);
		});

		it('returns paginated results with custom page and limit', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createFlock(app, user.farmId, speciesId, breedId, { name: 'Flock 1' });
			await createFlock(app, user.farmId, speciesId, breedId, { name: 'Flock 2' });
			await createFlock(app, user.farmId, speciesId, breedId, { name: 'Flock 3' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/flocks?language=en&page=1&limit=2',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(2);
			expect(body.meta.pagination.total).toBe(3);
			expect(body.meta.pagination.totalPages).toBe(2);
		});

		it('filters flocks by status', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createFlock(app, user.farmId, speciesId, breedId, { name: 'Active Flock', status: 'active' });
			await createFlock(app, user.farmId, speciesId, breedId, { name: 'Sold Flock', status: 'sold' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/flocks?language=en&status=active',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(1);
			expect(body.data[0].status).toBe('active');
		});

		it('filters flocks by flockType', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createFlock(app, user.farmId, speciesId, breedId, { name: 'Layer Flock', flockType: 'layers' });
			await createFlock(app, user.farmId, speciesId, breedId, { name: 'General Flock', flockType: 'general' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/flocks?language=en&flockType=layers',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(1);
			expect(body.data[0].flockType).toBe('layers');
		});
	});

	describe('POST /api/v1/flocks', () => {
		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/flocks',
				payload: {
					name: 'Test Flock',
					speciesId: 'fakeid',
					breedId: 'fakeid',
					flockType: 'general',
					initialCount: 50,
					startDate: '2025-01-01',
					acquisitionType: 'purchased',
					language: 'en',
				},
			});

			expect(response.statusCode).toBe(401);
		});

		it('creates a new flock with currentCount equal to initialCount', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/flocks',
				headers: { cookie },
				payload: {
					name: 'New Flock',
					speciesId: encodeId(speciesId),
					breedId: encodeId(breedId),
					flockType: 'layers',
					initialCount: 75,
					startDate: '2025-06-01',
					acquisitionType: 'purchased',
					language: 'en',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data.name).toBe('New Flock');
			expect(body.data.initialCount).toBe(75);
			expect(body.data.currentCount).toBe(75);
			expect(typeof body.data.id).toBe('string');
		});

		it('returns flock with species and breed includes', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app, { name: 'Chicken' });
			const { breedId } = await createBreed(app, speciesId, { name: 'Leghorn' });

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/flocks',
				headers: { cookie },
				payload: {
					name: 'Include Flock',
					speciesId: encodeId(speciesId),
					breedId: encodeId(breedId),
					flockType: 'general',
					initialCount: 50,
					startDate: '2025-01-01',
					acquisitionType: 'purchased',
					language: 'en',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.species).toBeDefined();
			expect(body.data.species.translations).toHaveLength(1);
			expect(body.data.species.translations[0].name).toBe('Chicken');
			expect(body.data.breed).toBeDefined();
			expect(body.data.breed.translations).toHaveLength(1);
			expect(body.data.breed.translations[0].name).toBe('Leghorn');
		});

		it('rejects duplicate name on same farm', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);

			await app.inject({
				method: 'POST',
				url: '/api/v1/flocks',
				headers: { cookie },
				payload: {
					name: 'Duplicate Flock',
					speciesId: encodeId(speciesId),
					breedId: encodeId(breedId),
					flockType: 'general',
					initialCount: 50,
					startDate: '2025-01-01',
					acquisitionType: 'purchased',
					language: 'en',
				},
			});

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/flocks',
				headers: { cookie },
				payload: {
					name: 'Duplicate Flock',
					speciesId: encodeId(speciesId),
					breedId: encodeId(breedId),
					flockType: 'general',
					initialCount: 30,
					startDate: '2025-02-01',
					acquisitionType: 'purchased',
					language: 'en',
				},
			});

			expect(response.statusCode).toBe(400);
			const body = response.json();
			expect(body.message).toContain('already exists');
		});

		it('rejects mismatched breed and species', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			const { speciesId: species1Id } = await createSpecies(app, { name: 'Chicken' });
			const { speciesId: species2Id } = await createSpecies(app, { name: 'Duck' });
			const { breedId } = await createBreed(app, species2Id, { name: 'Pekin' });

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/flocks',
				headers: { cookie },
				payload: {
					name: 'Mismatch Flock',
					speciesId: encodeId(species1Id),
					breedId: encodeId(breedId),
					flockType: 'general',
					initialCount: 50,
					startDate: '2025-01-01',
					acquisitionType: 'purchased',
					language: 'en',
				},
			});

			expect(response.statusCode).toBe(400);
			const body = response.json();
			expect(body.message).toContain('does not belong');
		});
	});

	describe('GET /api/v1/flocks/:id', () => {
		it('returns a single flock by id', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			const { encodedFlockId } = await createFlock(app, user.farmId, speciesId, breedId, { name: 'Finder Flock' });

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/flocks/${encodedFlockId}?language=en`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.name).toBe('Finder Flock');
		});

		it('returns 404 for non-existent flock', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/flocks/${encodeId(99999)}?language=en`,
				headers: { cookie },
			});

			expect(response.statusCode).toBe(404);
		});
	});

	describe('PUT /api/v1/flocks/:id', () => {
		it('updates flock fields', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			const { encodedFlockId } = await createFlock(app, user.farmId, speciesId, breedId, { name: 'Old Name' });

			const response = await app.inject({
				method: 'PUT',
				url: `/api/v1/flocks/${encodedFlockId}`,
				headers: { cookie },
				payload: {
					name: 'New Name',
					status: 'sold',
					houseName: 'Barn C',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.name).toBe('New Name');
			expect(body.data.status).toBe('sold');
			expect(body.data.houseName).toBe('Barn C');
		});

		it('rejects duplicate name on update', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createFlock(app, user.farmId, speciesId, breedId, { name: 'Taken Name' });
			const { encodedFlockId } = await createFlock(app, user.farmId, speciesId, breedId, { name: 'Other Flock' });

			const response = await app.inject({
				method: 'PUT',
				url: `/api/v1/flocks/${encodedFlockId}`,
				headers: { cookie },
				payload: {
					name: 'Taken Name',
				},
			});

			expect(response.statusCode).toBe(400);
			const body = response.json();
			expect(body.message).toContain('already exists');
		});
	});

	describe('DELETE /api/v1/flocks/:id', () => {
		it('deletes a flock', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			const { encodedFlockId } = await createFlock(app, user.farmId, speciesId, breedId, { name: 'To Delete' });

			const response = await app.inject({
				method: 'DELETE',
				url: `/api/v1/flocks/${encodedFlockId}`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
		});

		it('returns 404 for non-existent flock', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'DELETE',
				url: `/api/v1/flocks/${encodeId(99999)}`,
				headers: { cookie },
			});

			expect(response.statusCode).toBe(404);
		});
	});
});
