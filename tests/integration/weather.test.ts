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
			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/weather?latitude=-34.6&longitude=-58.4',
			});

			expect(response.statusCode).toBe(401);
		});

		it('returns 400 when latitude is missing', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/weather?longitude=-58.4',
				headers: { cookie },
			});

			expect(response.statusCode).toBe(400);
		});

		it('returns 400 when longitude is missing', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/weather?latitude=-34.6',
				headers: { cookie },
			});

			expect(response.statusCode).toBe(400);
		});

		it('returns 400 when latitude is out of range', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/weather?latitude=999&longitude=-58.4',
				headers: { cookie },
			});

			expect(response.statusCode).toBe(400);
		});

		it('returns 400 when longitude is out of range', async () => {
			const { cookie } = await createAuthenticatedUser(app);

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/weather?latitude=-34.6&longitude=999',
				headers: { cookie },
			});

			expect(response.statusCode).toBe(400);
		});

		it('returns weather data for valid coordinates', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			const mockData = createOpenMeteoResponse();
			fetchSpy = vi.spyOn(globalThis, 'fetch');
			fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(mockData), { status: 200 }));

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/weather?latitude=-34.6&longitude=-58.4',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(200);
			expect(body.status).toBe('success');
			expect(body.message).toBe('Weather data retrieved successfully');
			expect(body.data.current).toBeDefined();
			expect(body.data.daily).toBeDefined();
			expect(body.data.location).toBeDefined();
			expect(body.data.units).toBeDefined();
		});

		it('returns current weather with correct fields', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			const mockData = createOpenMeteoResponse();
			fetchSpy = vi.spyOn(globalThis, 'fetch');
			fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(mockData), { status: 200 }));

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/weather?latitude=-34.6&longitude=-58.4',
				headers: { cookie },
			});

			const { current } = response.json().data;
			expect(current.temperature).toBe(22.5);
			expect(current.apparentTemperature).toBe(24.4);
			expect(current.weatherCode).toBe(0);
			expect(current.weatherDescription).toBe('Clear sky');
			expect(current.windSpeed).toBe(4);
			expect(current.humidity).toBe(66);
			expect(current.precipitation).toBe(0);
		});

		it('returns daily forecast array with correct fields', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			const mockData = createOpenMeteoResponse();
			fetchSpy = vi.spyOn(globalThis, 'fetch');
			fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(mockData), { status: 200 }));

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/weather?latitude=-34.6&longitude=-58.4',
				headers: { cookie },
			});

			const { daily } = response.json().data;
			expect(daily).toHaveLength(1);
			expect(daily[0].date).toBe('2026-03-26');
			expect(daily[0].temperatureMax).toBe(26.8);
			expect(daily[0].temperatureMin).toBe(12.4);
			expect(daily[0].sunrise).toBe('2026-03-26T07:02');
			expect(daily[0].sunset).toBe('2026-03-26T18:57');
			expect(daily[0].uvIndexMax).toBe(6.65);
		});

		it('returns 502 when Open-Meteo API is unreachable', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			fetchSpy = vi.spyOn(globalThis, 'fetch');
			fetchSpy.mockRejectedValueOnce(new TypeError('fetch failed'));

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/weather?latitude=-34.6&longitude=-58.4',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(502);
			expect(body.status).toBe('error');
			expect(body.message).toBe('Weather data unavailable');
		});

		it('returns 502 when Open-Meteo returns an error status', async () => {
			const { cookie } = await createAuthenticatedUser(app);
			fetchSpy = vi.spyOn(globalThis, 'fetch');
			fetchSpy.mockResolvedValueOnce(new Response(
				JSON.stringify({ reason: 'Bad request' }),
				{ status: 400 },
			));

			const response = await app.inject({
				method: 'GET',
				url: '/api/v1/weather?latitude=-34.6&longitude=-58.4',
				headers: { cookie },
			});

			const body = response.json();
			expect(response.statusCode).toBe(502);
			expect(body.status).toBe('error');
			expect(body.message).toBe('Weather data unavailable');
		});
	});
});
