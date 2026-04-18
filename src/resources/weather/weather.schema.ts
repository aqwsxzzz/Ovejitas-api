import { Static, Type } from '@sinclair/typebox';
import { createGetEndpointSchema } from '../../utils/schema-builder';

// ── Response: Current Weather ───────────────────────────────────────

const CurrentWeatherSchema = Type.Object({
	temperature: Type.Number(),
	apparentTemperature: Type.Number(),
	weatherCode: Type.Integer(),
	weatherDescription: Type.String(),
	windSpeed: Type.Number(),
	humidity: Type.Number(),
	precipitation: Type.Number(),
});

// ── Response: Daily Forecast ────────────────────────────────────────

const DailyForecastSchema = Type.Object({
	date: Type.String(),
	temperatureMax: Type.Number(),
	temperatureMin: Type.Number(),
	precipitationSum: Type.Number(),
	precipitationProbabilityMax: Type.Integer(),
	windSpeedMax: Type.Number(),
	weatherCode: Type.Integer(),
	weatherDescription: Type.String(),
	sunrise: Type.String(),
	sunset: Type.String(),
	uvIndexMax: Type.Number(),
});

// ── Response: Full Weather ──────────────────────────────────────────

const WeatherLocationSchema = Type.Object({
	latitude: Type.Number(),
	longitude: Type.Number(),
});

const WeatherUnitsSchema = Type.Object({
	temperature: Type.String(),
	windSpeed: Type.String(),
	precipitation: Type.String(),
	humidity: Type.String(),
});

export const WeatherResponseSchema = Type.Object({
	current: CurrentWeatherSchema,
	daily: Type.Array(DailyForecastSchema),
	location: WeatherLocationSchema,
	units: WeatherUnitsSchema,
}, { $id: 'weatherResponse', additionalProperties: false });

export type WeatherResponse = Static<typeof WeatherResponseSchema>;

// ── Route Schema ────────────────────────────────────────────────────

export const getWeatherSchema = createGetEndpointSchema({
	dataSchema: WeatherResponseSchema,
	errorCodes: [400, 404, 502],
});
