import { FastifyPluginAsync } from 'fastify';
import animalMeasurementRoutes from './animal-measurement.routes';

const animalMeasurementPlugin: FastifyPluginAsync = async (fastify) => {
	// Note: This is a nested resource under animals, so no additional prefix needed
	await fastify.register(animalMeasurementRoutes);
};

export default animalMeasurementPlugin;
