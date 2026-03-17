import { FastifyInstance, FastifyPluginAsync, FastifyRequest } from 'fastify';
import { AnimalMeasurementParams, AnimalMeasurementDeleteParams, AnimalMeasurementCreate, listAnimalMeasurementsSchema, latestAnimalMeasurementsSchema, createAnimalMeasurementSchema, deleteAnimalMeasurementSchema, AnimalMeasurementQuery } from './animal-measurement.schema';
import { decodeId } from '../../utils/id-hash-util';
import { AnimalMeasurementSerializer } from './animal-measurement.serializer';
import { parsePagination } from '../../utils/pagination';

const animalMeasurementRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	fastify.get('/animals/:animalId/measurements/latest', { schema: latestAnimalMeasurementsSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Params: AnimalMeasurementParams}>, reply) => {
		try {
			const { animalId } = request.params;
			const measurements = await fastify.animalMeasurementService.getLatestMeasurements(decodeId(animalId)!);
			const serialized = AnimalMeasurementSerializer.serializeMany(measurements);
			reply.success(serialized);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/animals/:animalId/measurements', { schema: listAnimalMeasurementsSchema, preHandler: fastify.authenticate }, async (request: FastifyRequest<{Params: AnimalMeasurementParams, Querystring: AnimalMeasurementQuery}>, reply) => {
		try {
			const { animalId } = request.params;
			const { measurementType } = request.query;
			const pagination = parsePagination(request.query);
			const result = await fastify.animalMeasurementService.getAnimalMeasurements(decodeId(animalId)!, '', { measurementType: measurementType as string }, pagination);
			const serializedMeasurements = measurementType
				? AnimalMeasurementSerializer.serializeManyWithDeltas(result.rows)
				: AnimalMeasurementSerializer.serializeMany(result.rows).map(m => ({ ...m, change: null, changePercent: null }));
			reply.successWithPagination(serializedMeasurements, result.pagination);
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
