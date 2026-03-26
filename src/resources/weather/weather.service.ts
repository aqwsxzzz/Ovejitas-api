import { WeatherResponse } from './weather.schema';

// ── Open-Meteo Raw Response Types ───────────────────────────────────

interface OpenMeteoCurrentResponse {
	temperature_2m: number;
	apparent_temperature: number;
	weather_code: number;
	wind_speed_10m: number;
	relative_humidity_2m: number;
	precipitation: number;
}

interface OpenMeteoDailyResponse {
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
}

interface OpenMeteoResponse {
	latitude: number;
	longitude: number;
	current: OpenMeteoCurrentResponse;
	current_units: Record<string, string>;
	daily: OpenMeteoDailyResponse;
	daily_units: Record<string, string>;
	error?: boolean;
	reason?: string;
}

// ── WMO Weather Code Descriptions ──────────────────────────────────

const WMO_CODES: Record<number, string> = {
	0: 'Clear sky',
	1: 'Mainly clear',
	2: 'Partly cloudy',
	3: 'Overcast',
	45: 'Fog',
	48: 'Depositing rime fog',
	51: 'Light drizzle',
	53: 'Moderate drizzle',
	55: 'Dense drizzle',
	56: 'Light freezing drizzle',
	57: 'Dense freezing drizzle',
	61: 'Slight rain',
	63: 'Moderate rain',
	65: 'Heavy rain',
	66: 'Light freezing rain',
	67: 'Heavy freezing rain',
	71: 'Slight snowfall',
	73: 'Moderate snowfall',
	75: 'Heavy snowfall',
	77: 'Snow grains',
	80: 'Slight rain showers',
	81: 'Moderate rain showers',
	82: 'Violent rain showers',
	85: 'Slight snow showers',
	86: 'Heavy snow showers',
	95: 'Thunderstorm',
	96: 'Thunderstorm with slight hail',
	99: 'Thunderstorm with heavy hail',
};

// ── Weather Service ─────────────────────────────────────────────────

const OPEN_METEO_BASE_URL = 'https://api.open-meteo.com/v1/forecast';
const CURRENT_PARAMS = 'temperature_2m,apparent_temperature,weather_code,wind_speed_10m,relative_humidity_2m,precipitation';
const DAILY_PARAMS = 'temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,weather_code,sunrise,sunset,uv_index_max';
const TIMEOUT_MS = 10_000;

export class WeatherService {
	async getWeather(latitude: number, longitude: number): Promise<WeatherResponse> {
		const url = this.buildUrl(latitude, longitude);
		const raw = await this.fetchWeatherData(url);
		return this.transformResponse(raw);
	}

	private buildUrl(latitude: number, longitude: number): string {
		const params = new URLSearchParams({
			latitude: String(latitude),
			longitude: String(longitude),
			current: CURRENT_PARAMS,
			daily: DAILY_PARAMS,
			timezone: 'auto',
			forecast_days: '7',
		});

		return `${OPEN_METEO_BASE_URL}?${params.toString()}`;
	}

	private async fetchWeatherData(url: string): Promise<OpenMeteoResponse> {
		const response = await fetch(url, {
			signal: AbortSignal.timeout(TIMEOUT_MS),
		});

		if (!response.ok) {
			const body = await response.json().catch(() => null) as { reason?: string } | null;
			const reason = body?.reason ?? `HTTP ${response.status}`;
			throw new Error(`Open-Meteo API error: ${reason}`);
		}

		const data = await response.json() as OpenMeteoResponse;

		if (data.error) {
			throw new Error(`Open-Meteo API error: ${data.reason ?? 'Unknown error'}`);
		}

		return data;
	}

	private transformResponse(raw: OpenMeteoResponse): WeatherResponse {
		const { current, daily } = raw;

		return {
			current: {
				temperature: current.temperature_2m,
				apparentTemperature: current.apparent_temperature,
				weatherCode: current.weather_code,
				weatherDescription: this.getWeatherDescription(current.weather_code),
				windSpeed: current.wind_speed_10m,
				humidity: current.relative_humidity_2m,
				precipitation: current.precipitation,
			},
			daily: daily.time.map((date, i) => ({
				date,
				temperatureMax: daily.temperature_2m_max[i],
				temperatureMin: daily.temperature_2m_min[i],
				precipitationSum: daily.precipitation_sum[i],
				precipitationProbabilityMax: daily.precipitation_probability_max[i],
				windSpeedMax: daily.wind_speed_10m_max[i],
				weatherCode: daily.weather_code[i],
				weatherDescription: this.getWeatherDescription(daily.weather_code[i]),
				sunrise: daily.sunrise[i],
				sunset: daily.sunset[i],
				uvIndexMax: daily.uv_index_max[i],
			})),
			location: {
				latitude: raw.latitude,
				longitude: raw.longitude,
			},
			units: {
				temperature: raw.current_units.temperature_2m ?? '°C',
				windSpeed: raw.current_units.wind_speed_10m ?? 'km/h',
				precipitation: raw.current_units.precipitation ?? 'mm',
				humidity: raw.current_units.relative_humidity_2m ?? '%',
			},
		};
	}

	private getWeatherDescription(code: number): string {
		return WMO_CODES[code] ?? 'Unknown';
	}
}
