import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';
import { createSpecies, createBreed, createAnimal, createMeasurement } from '../helpers/factories';

describe('Animal Measurement endpoints', () => {
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

	describe('GET /api/v1/animals/:animalId/measurements/latest', () => {
		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/animals/fakeid/measurements/latest',
			});

			expect(response.statusCode).toBe(401);
		});

		it('returns empty array when animal has no measurements', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			const { encodedAnimalId } = await createAnimal(app, user.farmId, speciesId, breedId);

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/animals/${encodedAnimalId}/measurements/latest`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.data).toHaveLength(0);
		});

		it('returns latest measurement per type', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			const { animalId, encodedAnimalId } = await createAnimal(app, user.farmId, speciesId, breedId);

			// Create older weight
			await createMeasurement(app, animalId, user.id, {
				measurementType: 'weight', value: 40, unit: 'kg', measuredAt: '2025-01-01T00:00:00Z',
			});
			// Create newer weight (should be returned)
			await createMeasurement(app, animalId, user.id, {
				measurementType: 'weight', value: 50, unit: 'kg', measuredAt: '2025-06-01T00:00:00Z',
			});
			// Create a height measurement
			await createMeasurement(app, animalId, user.id, {
				measurementType: 'height', value: 80, unit: 'cm', measuredAt: '2025-03-01T00:00:00Z',
			});

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/animals/${encodedAnimalId}/measurements/latest`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(2);

			const types = body.data.map((m: { measurementType: string }) => m.measurementType).sort();
			expect(types).toEqual(['height', 'weight']);

			const weight = body.data.find((m: { measurementType: string }) => m.measurementType === 'weight');
			expect(weight.value).toBe(50);
		});

		it('returns only types with data', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			const { animalId, encodedAnimalId } = await createAnimal(app, user.farmId, speciesId, breedId);

			await createMeasurement(app, animalId, user.id, {
				measurementType: 'temperature', value: 38.5, unit: 'celsius', measuredAt: '2025-01-01T00:00:00Z',
			});

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/animals/${encodedAnimalId}/measurements/latest`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(1);
			expect(body.data[0].measurementType).toBe('temperature');
			expect(body.data[0].value).toBe(38.5);
		});
	});

	describe('GET /api/v1/animals/:animalId/measurements (history with deltas)', () => {
		it('returns change and changePercent when measurementType filter is provided', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			const { animalId, encodedAnimalId } = await createAnimal(app, user.farmId, speciesId, breedId);

			await createMeasurement(app, animalId, user.id, {
				measurementType: 'weight', value: 40, unit: 'kg', measuredAt: '2025-01-01T00:00:00Z',
			});
			await createMeasurement(app, animalId, user.id, {
				measurementType: 'weight', value: 50, unit: 'kg', measuredAt: '2025-02-01T00:00:00Z',
			});
			await createMeasurement(app, animalId, user.id, {
				measurementType: 'weight', value: 45, unit: 'kg', measuredAt: '2025-03-01T00:00:00Z',
			});

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/animals/${encodedAnimalId}/measurements?measurementType=weight`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data).toHaveLength(3);

			// Results are DESC order (newest first)
			// Most recent: 45kg (change from 50 = -5)
			expect(body.data[0].value).toBe(45);
			expect(body.data[0].change).toBe(-5);
			expect(body.data[0].changePercent).toBe(-10);

			// Middle: 50kg (change from 40 = +10)
			expect(body.data[1].value).toBe(50);
			expect(body.data[1].change).toBe(10);
			expect(body.data[1].changePercent).toBe(25);
		});

		it('first (oldest) measurement has null change and changePercent', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			const { animalId, encodedAnimalId } = await createAnimal(app, user.farmId, speciesId, breedId);

			await createMeasurement(app, animalId, user.id, {
				measurementType: 'weight', value: 40, unit: 'kg', measuredAt: '2025-01-01T00:00:00Z',
			});
			await createMeasurement(app, animalId, user.id, {
				measurementType: 'weight', value: 50, unit: 'kg', measuredAt: '2025-02-01T00:00:00Z',
			});

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/animals/${encodedAnimalId}/measurements?measurementType=weight`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);

			// Oldest measurement (last in DESC order) has null deltas
			const oldest = body.data[body.data.length - 1];
			expect(oldest.value).toBe(40);
			expect(oldest.change).toBeNull();
			expect(oldest.changePercent).toBeNull();
		});

		it('does not include deltas when no measurementType filter', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			const { speciesId } = await createSpecies(app);
			const { breedId } = await createBreed(app, speciesId);
			const { animalId, encodedAnimalId } = await createAnimal(app, user.farmId, speciesId, breedId);

			await createMeasurement(app, animalId, user.id, {
				measurementType: 'weight', value: 40, unit: 'kg', measuredAt: '2025-01-01T00:00:00Z',
			});

			const response = await app.inject({
				method: 'GET',
				url: `/api/v1/animals/${encodedAnimalId}/measurements`,
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data[0].change).toBeNull();
			expect(body.data[0].changePercent).toBeNull();
		});
	});
});
