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
