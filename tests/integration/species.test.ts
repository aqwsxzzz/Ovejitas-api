import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import { createSpecies } from '../helpers/factories';

describe('Species endpoints', () => {
	let app: FastifyInstance;
	let cookie: string;

	beforeAll(async () => {
		app = await createTestApp();
	});

	afterEach(async () => {
		await truncateAllTables(app);
	});

	afterAll(async () => {
		await app.close();
	});

	describe('GET /api/v1/species', () => {
		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/species?language=en',
			});

			expect(response.statusCode).toBe(401);
		});

		it('returns all species with default pagination', async () => {
			const auth = await createAuthenticatedUser(app);
			cookie = auth.cookie;

			await createSpecies(app, { name: 'Sheep', language: 'en' });
			await createSpecies(app, { name: 'Goat', language: 'en' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/species?language=en',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data).toHaveLength(2);
			expect(body.meta.pagination).toBeDefined();
			expect(body.meta.pagination.page).toBe(1);
			expect(body.meta.pagination.limit).toBe(20);
			expect(body.meta.pagination.total).toBe(2);
		});

		it('returns paginated results with meta when page and limit are provided', async () => {
			const auth = await createAuthenticatedUser(app);
			cookie = auth.cookie;

			await createSpecies(app, { name: 'Sheep', language: 'en' });
			await createSpecies(app, { name: 'Goat', language: 'en' });
			await createSpecies(app, { name: 'Cow', language: 'en' });

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/species?language=en&page=1&limit=2',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data).toHaveLength(2);
			expect(body.meta.pagination).toBeDefined();
			expect(body.meta.pagination.page).toBe(1);
			expect(body.meta.pagination.limit).toBe(2);
			expect(body.meta.pagination.total).toBe(3);
			expect(body.meta.pagination.totalPages).toBe(2);
		});
	});

	describe('POST /api/v1/species', () => {
		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/species',
				payload: { name: 'Sheep', language: 'en' },
			});

			expect(response.statusCode).toBe(401);
		});

		it('creates a new species and returns it', async () => {
			const auth = await createAuthenticatedUser(app);
			cookie = auth.cookie;

			const response = await app.inject({
				method: 'POST',
				url: '/api/v1/species',
				payload: { name: 'Sheep', language: 'en' },
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data.id).toBeDefined();
			expect(typeof body.data.id).toBe('string');
		});
	});
});
