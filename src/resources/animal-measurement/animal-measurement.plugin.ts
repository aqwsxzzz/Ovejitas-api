import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { AnimalMeasurementService } from './animal-measurement.service';
import { AnimalMeasurementParams, listAnimalMeasurementsSchema } from './animal-measurement.schema';
import { decodeId } from '../../utils/id-hash-util';

const animalMeasurementPlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {
	const animalMeasurementService = new AnimalMeasurementService(fastify.db);

	fastify.get('/animals/:animalId/measurements', { schema: listAnimalMeasurementsSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Params: AnimalMeasurementParams}>, reply) => {
		try {
			const { animalId } = request.params;
			const measurements = await animalMeasurementService.getAnimalMeasurements(decodeId(animalId)!);
			reply.success(measurements);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

};

export default animalMeasurementPlugin;
