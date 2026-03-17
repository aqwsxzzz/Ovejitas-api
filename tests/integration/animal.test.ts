import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import { createSpecies, createBreed, createAnimal } from '../helpers/factories';
import { encodeId } from '../../src/utils/id-hash-util';

describe('Animal endpoints', () => {
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

	describe('GET /api/v1/animals', () => {
		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals?language=en',
			});

			expect(response.statusCode).toBe(401);
		});

		it('returns animals with default pagination', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'A-001', name: 'Dolly' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'A-002', name: 'Molly' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals?language=en',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data).toHaveLength(2);
			expect(body.meta.pagination).toBeDefined();
			expect(body.meta.pagination.total).toBe(2);
		});

		it('returns paginated results when page and limit provided', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'A-001' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'A-002' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'A-003' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals?language=en&page=1&limit=2',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(2);
			expect(body.meta.pagination).toBeDefined();
			expect(body.meta.pagination.total).toBe(3);
			expect(body.meta.pagination.totalPages).toBe(2);
		});

		it('filters animals by sex', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'M-001', sex: 'male' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'F-001', sex: 'female' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals?language=en&sex=female',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(1);
		});
	});

	describe('GET /api/v1/animals/search', () => {
		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals/search?q=test&language=en',
			});

			expect(response.statusCode).toBe(401);
		});

		it('returns 400 when q parameter is missing', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals/search?language=en',
				headers: { cookie },
			});

			expect(response.statusCode).toBe(400);
		});

		it('matches animals by name', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'S-001', name: 'Dolly' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'S-002', name: 'Molly' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'S-003', name: 'Berta' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals/search?q=olly&language=en',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data).toHaveLength(2);
		});

		it('matches animals by tagNumber', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'TAG-100', name: 'Alpha' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'TAG-200', name: 'Beta' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'OTHER-001', name: 'Gamma' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals/search?q=TAG&language=en',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(2);
		});

		it('matches animals by groupName', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'G-001', groupName: 'Barn A' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'G-002', groupName: 'Barn B' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'G-003', groupName: 'Pasture' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals/search?q=barn&language=en',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(2);
		});

		it('is case-insensitive', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'CI-001', name: 'DOLLY' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals/search?q=dolly&language=en',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(1);
		});

		it('combines search with sex filter', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'SF-001', name: 'Dolly', sex: 'female' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'SF-002', name: 'Dollar', sex: 'male' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals/search?q=dol&sex=female&language=en',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(1);
			expect(body.data[0].tagNumber).toBe('SF-001');
		});

		it('returns paginated search results', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'P-001', name: 'Sheep One' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'P-002', name: 'Sheep Two' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'P-003', name: 'Sheep Three' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals/search?q=sheep&language=en&page=1&limit=2',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(2);
			expect(body.meta.pagination.total).toBe(3);
			expect(body.meta.pagination.totalPages).toBe(2);
		});

		it('returns empty results when no matches found', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'NM-001', name: 'Dolly' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals/search?q=zzzznotfound&language=en',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(0);
			expect(body.meta.pagination.total).toBe(0);
		});
	});

	describe('GET /api/v1/animals/stats', () => {
		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals/stats',
			});

			expect(response.statusCode).toBe(401);
		});

		it('returns total count and lastSevenDays count', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'ST-001' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'ST-002' });
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'ST-003' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals/stats',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data.total).toBe(3);
			expect(body.data.lastSevenDays).toBe(3);
		});

		it('lastSevenDays only counts animals created within 7 days', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);

			// Create a recent animal (within 7 days — default created_at is now)
			await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'REC-001' });

			// Create an old animal by directly updating created_at
			const { animalId } = await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'OLD-001' });
			await app.db.models.Animal.update(
				{ createdAt: new Date('2020-01-01') },
				{ where: { id: animalId }, silent: true },
			);

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals/stats',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.total).toBe(2);
			expect(body.data.lastSevenDays).toBe(1);
		});
	});

	describe('POST /api/v1/animals', () => {
		it('returns 401 when not authenticated with valid body', async () => {
			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/animals',
				payload: {
					speciesId: 'fakeid',
					breedId: 'fakeid',
					tagNumber: 'TEST-001',
					language: 'en',
				},
			});

			expect(response.statusCode).toBe(401);
		});

		it('creates a new animal', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/animals',
				headers: { cookie },
				payload: {
					speciesId: encodeId(speciesId),
					breedId: encodeId(breedId),
					tagNumber: 'NEW-001',
					language: 'en',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data.tagNumber).toBe('NEW-001');
			expect(typeof body.data.id).toBe('string');
		});

		it('rejects duplicate tag number for same farm and species', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);

			await app.inject({
				method: 'POST',
				url: '/api/v1/animals',
				headers: { cookie },
				payload: {
					speciesId: encodeId(speciesId),
					breedId: encodeId(breedId),
					tagNumber: 'DUP-001',
					language: 'en',
				},
			});

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/animals',
				headers: { cookie },
				payload: {
					speciesId: encodeId(speciesId),
					breedId: encodeId(breedId),
					tagNumber: 'DUP-001',
					language: 'en',
				},
			});

			expect(response.statusCode).toBe(400);
			const body = response.json();
			expect(body.message).toContain('Tag number');
		});
	});

	describe('GET /api/v1/animals/:id', () => {
		it('returns a single animal by id', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			const { encodedAnimalId } = await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'GET-001', name: 'Finder' });

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/animals/${encodedAnimalId}?language=en`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.tagNumber).toBe('GET-001');
			expect(body.data.name).toBe('Finder');
		});
	});

	describe('PUT /api/v1/animals/:id', () => {
		it('updates an existing animal', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			const { encodedAnimalId } = await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'UPD-001' });

			const response = await app.inject({
				method: 'PUT',
				url: `/api/v1/animals/${encodedAnimalId}`,
				headers: { cookie },
				payload: {
					speciesId: encodeId(speciesId),
					breedId: encodeId(breedId),
					tagNumber: 'UPD-001',
					name: 'Updated Name',
				},
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.name).toBe('Updated Name');
		});
	});

	describe('DELETE /api/v1/animals/:id', () => {
		it('deletes an animal', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			const { encodedAnimalId } = await createAnimal(app, user.farmId, speciesId, breedId, { tagNumber: 'DEL-001' });

			const response = await app.inject({
				method: 'DELETE',
				url: `/api/v1/animals/${encodedAnimalId}`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
		});

		it('returns 404 for non-existent animal', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'DELETE',
				url: '/api/v1/animals/nonexistentid',
				headers: { cookie },
			});

			expect(response.statusCode).toBe(400);
		});
	});
});
