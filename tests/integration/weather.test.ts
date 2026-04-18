import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { FastifyInstance } from 'fastify';
import { createTestApp } from '../helpers/build-app';
import { createAuthenticatedUser } from '../helpers/auth';
import { truncateAllTables } from '../helpers/truncate';

function createOpenMeteoResponse() {
	return {
		latitude: -34.625,
		longitude: -58.5,
		current: {
			temperature_2m: 22.5,
			apparent_temperature: 24.4,
			weather_code: 0,
			wind_speed_10m: 4,
			relative_humidity_2m: 66,
			precipitation: 0,
		},
		current_units: {
			temperature_2m: '°C',
			wind_speed_10m: 'km/h',
			precipitation: 'mm',
			relative_humidity_2m: '%',
		},
		daily: {
			time: ['2026-03-26'],
			temperature_2m_max: [26.8],
			temperature_2m_min: [12.4],
			precipitation_sum: [0],
			precipitation_probability_max: [0],
			wind_speed_10m_max: [11.2],
			weather_code: [2],
			sunrise: ['2026-03-26T07:02'],
			sunset: ['2026-03-26T18:57'],
			uv_index_max: [6.65],
		},
	};
}

async function setFarmLocation(app: FastifyInstance, farmId: number, latitude: number, longitude: number) {
	await app.db.models.Farm.update({ latitude, longitude }, { where: { id: farmId } });
}

describe('Weather endpoints', () => {
	let app: FastifyInstance;
	let fetchSpy: ReturnType<typeof vi.spyOn>;

	beforeAll(async () => {
		app = await createTestApp();
	});

	afterEach(async () => {
		vi.restoreAllMocks();
		await truncateAllTables(app);
	});

	afterAll(async () => {
		await app.close();
	});

	describe('GET /api/v1/weather', () => {
		it('returns 401 when not authenticated', async () => {
			const response = await app.inject({ method: 'GET', url: '/api/v1/weather' });
			expect(response.statusCode).toBe(401);
		});

		it('returns 400 when farm location is not set', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/weather',
				headers: { cookie },
			});

			expect(response.statusCode).toBe(400);
			expect(response.json().message).toMatch(/location is not set/i);
		});

		it('returns weather data using the farm coordinates', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			await setFarmLocation(app, user.farmId, -34.6, -58.4);

			const mockData = createOpenMeteoResponse();
			fetchSpy = vi.spyOn(globalThis, 'fetch');
			fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(mockData), { status: 200 }));

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/weather',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.data.current.temperature).toBe(22.5);
			expect(body.data.daily).toHaveLength(1);

			const fetchedUrl = fetchSpy.mock.calls[0]![0] as string;
			expect(fetchedUrl).toContain('latitude=-34.6');
			expect(fetchedUrl).toContain('longitude=-58.4');
		});

		it('returns 502 when Open-Meteo is unreachable', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			await setFarmLocation(app, user.farmId, -34.6, -58.4);

			fetchSpy = vi.spyOn(globalThis, 'fetch');
			fetchSpy.mockRejectedValueOnce(new TypeError('fetch failed'));

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/weather',
				headers: { cookie },
			});

			expect(response.statusCode).toBe(502);
			expect(response.json().message).toBe('Weather data unavailable');
		});

		it('returns 502 when Open-Meteo returns an error status', async () => {
			const { user, cookie } = await createAuthenticatedUser(app);
			await setFarmLocation(app, user.farmId, -34.6, -58.4);

			fetchSpy = vi.spyOn(globalThis, 'fetch');
			fetchSpy.mockResolvedValueOnce(new Response(
				JSON.stringify({ reason: 'Bad request' }),
				{ status: 400 },
			));

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/weather',
				headers: { cookie },
			});

			expect(response.statusCode).toBe(502);
			expect(response.json().message).toBe('Weather data unavailable');
		});
	});
});
