import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { AnimalMeasurementParams, listAnimalMeasurementsSchema } from './animal-measurement.schema';
import { decodeId } from '../../utils/id-hash-util';

const animalMeasurementRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {
	// Routes now use the decorated service instead of creating a new instance

	fastify.get('/animals/:animalId/measurements', { schema: listAnimalMeasurementsSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Params: AnimalMeasurementParams}>, reply) => {
		try {
			const { animalId } = request.params;
			const measurements = await fastify.animalMeasurementService.getAnimalMeasurements(decodeId(animalId)!);
			reply.success(measurements);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default animalMeasurementRoutes;
