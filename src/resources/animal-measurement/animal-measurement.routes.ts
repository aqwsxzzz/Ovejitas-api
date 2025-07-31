import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { AnimalMeasurementParams, AnimalMeasurementDeleteParams, AnimalMeasurementCreate, listAnimalMeasurementsSchema, createAnimalMeasurementSchema, deleteAnimalMeasurementSchema, AnimalMeasurementQuery } from './animal-measurement.schema';
import { decodeId } from '../../utils/id-hash-util';
import { AnimalMeasurementSerializer } from './animal-measurement.serializer';

const animalMeasurementRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {
	// Routes now use the decorated service instead of creating a new instance

	fastify.get('/animals/:animalId/measurements', { schema: listAnimalMeasurementsSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Params: AnimalMeasurementParams, Querystring: AnimalMeasurementQuery}>, reply) => {
		try {
			const { animalId } = request.params;
			const { measurementType } = request.query;

			const measurements = await fastify.animalMeasurementService.getAnimalMeasurements(decodeId(animalId)!, '', { measurementType: measurementType as string });
			const serializedMeasurements = AnimalMeasurementSerializer.serializeMany(measurements);
			reply.success(serializedMeasurements);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.post('/animals/:animalId/measurements', { schema: createAnimalMeasurementSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Params: AnimalMeasurementParams, Body: AnimalMeasurementCreate}>, reply) => {
		try {
			const { animalId } = request.params;
			const userId = request.user!.id;
			const measurement = await fastify.animalMeasurementService.createAnimalMeasurement({
				animalId: decodeId(animalId)!,
				data: request.body,
				userId,
			});
			const serializedMeasurement = AnimalMeasurementSerializer.serialize(measurement);
			reply.success(serializedMeasurement);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.delete('/animals/:animalId/measurements/:measurementId', { schema: deleteAnimalMeasurementSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Params: AnimalMeasurementDeleteParams}>, reply) => {
		try {
			const { animalId, measurementId } = request.params;
			await fastify.animalMeasurementService.deleteAnimalMeasurement({
				animalId: decodeId(animalId)!,
				measurementId: decodeId(measurementId)!,
			});
			reply.success(null);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default animalMeasurementRoutes;
