import { FastifyPluginAsync, FastifyRequest } from 'fastify';
import { getWeatherSchema, WeatherQuery } from './weather.schema';

const weatherRoutes: FastifyPluginAsync = async (fastify) => {
	fastify.get('/', {
		schema: getWeatherSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Querystring: WeatherQuery }>, reply) => {
		try {
			const { latitude, longitude } = request.query;
			const weather = await fastify.weatherService.getWeather(latitude, longitude);
			reply.success(weather, 'Weather data retrieved successfully');
		} catch (error) {
			fastify.log.error(error, 'Failed to fetch weather data from Open-Meteo');
			reply.error('Weather data unavailable', 502);
		}
	});
};

export default weatherRoutes;
