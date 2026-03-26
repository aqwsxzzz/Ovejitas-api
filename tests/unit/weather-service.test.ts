import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { WeatherService } from '../../src/resources/weather/weather.service';

// ── Open-Meteo mock response factory ────────────────────────────────

function createOpenMeteoResponse(overrides?: Partial<OpenMeteoMock>): OpenMeteoMock {
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
			time: ['2026-03-26', '2026-03-27'],
			temperature_2m_max: [26.8, 27.5],
			temperature_2m_min: [12.4, 18.2],
			precipitation_sum: [0, 2.5],
			precipitation_probability_max: [0, 43],
			wind_speed_10m_max: [11.2, 10.2],
			weather_code: [2, 61],
			sunrise: ['2026-03-26T07:02', '2026-03-27T07:02'],
			sunset: ['2026-03-26T18:57', '2026-03-27T18:55'],
			uv_index_max: [6.65, 5.9],
		},
		...overrides,
	};
}

interface OpenMeteoMock {
	latitude: number;
	longitude: number;
	error?: boolean;
	reason?: string;
	current: {
		temperature_2m: number;
		apparent_temperature: number;
		weather_code: number;
		wind_speed_10m: number;
		relative_humidity_2m: number;
		precipitation: number;
	};
	current_units: Record<string, string>;
	daily: {
		time: string[];
		temperature_2m_max: number[];
		temperature_2m_min: number[];
		precipitation_sum: number[];
		precipitation_probability_max: number[];
		wind_speed_10m_max: number[];
		weather_code: number[];
		sunrise: string[];
		sunset: string[];
		uv_index_max: number[];
	};
}

describe('WeatherService', () => {
	let service: WeatherService;
	let fetchSpy: ReturnType<typeof vi.spyOn>;

	beforeEach(() => {
		service = new WeatherService();
		fetchSpy = vi.spyOn(globalThis, 'fetch');
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	describe('getWeather', () => {
		it('returns transformed current weather and daily forecast', async () => {
			const mockData = createOpenMeteoResponse();
			fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(mockData), { status: 200 }));

			const result = await service.getWeather(-34.6, -58.4);

			expect(result.current.temperature).toBe(22.5);
			expect(result.current.apparentTemperature).toBe(24.4);
			expect(result.current.weatherCode).toBe(0);
			expect(result.current.weatherDescription).toBe('Clear sky');
			expect(result.current.windSpeed).toBe(4);
			expect(result.current.humidity).toBe(66);
			expect(result.current.precipitation).toBe(0);
		});

		it('returns correct number of daily forecasts', async () => {
			const mockData = createOpenMeteoResponse();
			fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(mockData), { status: 200 }));

			const result = await service.getWeather(-34.6, -58.4);

			expect(result.daily).toHaveLength(2);
		});

		it('transforms daily forecast fields from snake_case to camelCase', async () => {
			const mockData = createOpenMeteoResponse();
			fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(mockData), { status: 200 }));

			const result = await service.getWeather(-34.6, -58.4);
			const firstDay = result.daily[0];

			expect(firstDay.date).toBe('2026-03-26');
			expect(firstDay.temperatureMax).toBe(26.8);
			expect(firstDay.temperatureMin).toBe(12.4);
			expect(firstDay.precipitationSum).toBe(0);
			expect(firstDay.precipitationProbabilityMax).toBe(0);
			expect(firstDay.windSpeedMax).toBe(11.2);
			expect(firstDay.sunrise).toBe('2026-03-26T07:02');
			expect(firstDay.sunset).toBe('2026-03-26T18:57');
			expect(firstDay.uvIndexMax).toBe(6.65);
		});

		it('maps WMO weather codes to descriptions', async () => {
			const mockData = createOpenMeteoResponse();
			fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(mockData), { status: 200 }));

			const result = await service.getWeather(-34.6, -58.4);

			expect(result.daily[0].weatherDescription).toBe('Partly cloudy');
			expect(result.daily[1].weatherDescription).toBe('Slight rain');
		});

		it('returns "Unknown" for unrecognized WMO codes', async () => {
			const mockData = createOpenMeteoResponse();
			mockData.current.weather_code = 999;
			fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(mockData), { status: 200 }));

			const result = await service.getWeather(-34.6, -58.4);

			expect(result.current.weatherDescription).toBe('Unknown');
		});

		it('returns location echoing Open-Meteo resolved coordinates', async () => {
			const mockData = createOpenMeteoResponse();
			fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(mockData), { status: 200 }));

			const result = await service.getWeather(-34.6, -58.4);

			expect(result.location.latitude).toBe(-34.625);
			expect(result.location.longitude).toBe(-58.5);
		});

		it('returns measurement units from Open-Meteo response', async () => {
			const mockData = createOpenMeteoResponse();
			fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(mockData), { status: 200 }));

			const result = await service.getWeather(-34.6, -58.4);

			expect(result.units).toEqual({
				temperature: '°C',
				windSpeed: 'km/h',
				precipitation: 'mm',
				humidity: '%',
			});
		});

		it('calls Open-Meteo with correct URL parameters', async () => {
			const mockData = createOpenMeteoResponse();
			fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(mockData), { status: 200 }));

			await service.getWeather(-34.6, -58.4);

			expect(fetchSpy).toHaveBeenCalledOnce();
			const calledUrl = fetchSpy.mock.calls[0][0] as string;
			expect(calledUrl).toContain('latitude=-34.6');
			expect(calledUrl).toContain('longitude=-58.4');
			expect(calledUrl).toContain('timezone=auto');
			expect(calledUrl).toContain('forecast_days=7');
			expect(calledUrl).toContain('current=');
			expect(calledUrl).toContain('daily=');
		});

		it('throws when Open-Meteo returns non-ok HTTP status', async () => {
			fetchSpy.mockResolvedValueOnce(new Response(
				JSON.stringify({ reason: 'Invalid parameter' }),
				{ status: 400 },
			));

			await expect(service.getWeather(-34.6, -58.4))
				.rejects.toThrow('Open-Meteo API error: Invalid parameter');
		});

		it('throws when Open-Meteo returns error in response body', async () => {
			const errorResponse = {
				error: true,
				reason: 'Cannot initialize WeatherVariable from invalid String value',
			};
			fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(errorResponse), { status: 200 }));

			await expect(service.getWeather(-34.6, -58.4))
				.rejects.toThrow('Open-Meteo API error: Cannot initialize WeatherVariable from invalid String value');
		});

		it('throws when fetch fails due to network error', async () => {
			fetchSpy.mockRejectedValueOnce(new TypeError('fetch failed'));

			await expect(service.getWeather(-34.6, -58.4))
				.rejects.toThrow('fetch failed');
		});
	});
});
