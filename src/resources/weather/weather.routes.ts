import { FastifyPluginAsync } from 'fastify';
import { getWeatherSchema } from './weather.schema';

const weatherRoutes: FastifyPluginAsync = async (fastify) => {
	fastify.get('/', {
		schema: getWeatherSchema,
		preHandler: fastify.authenticate,
	}, async (request, reply) => {
		const farmId = request.lastVisitedFarmId;
		const farm = await fastify.db.models.Farm.findByPk(farmId);
		if (!farm) {
			return reply.error('Farm not found', 404);
		}

		const latitude = farm.latitude != null ? Number(farm.latitude) : null;
		const longitude = farm.longitude != null ? Number(farm.longitude) : null;
		if (latitude === null || longitude === null) {
			return reply.error('Farm location is not set. Configure latitude and longitude in farm settings.', 400);
		}

		try {
			const weather = await fastify.weatherService.getWeather(latitude, longitude);
			reply.success(weather, 'Weather data retrieved successfully');
		} catch (error) {
			fastify.log.error(error, 'Failed to fetch weather data from Open-Meteo');
			reply.error('Weather data unavailable', 502);
		}
	});
};

export default weatherRoutes;
