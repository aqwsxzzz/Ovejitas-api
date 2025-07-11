import { FastifyReply, FastifyRequest } from "fastify";
import { Op } from "sequelize";
import { AnimalMeasurement } from "../../models/animal-measurement-model";
import { Animal } from "../../models/animal-model";
import { serializeAnimalMeasurement } from "../../serializers/animal-measurement-serializer";
import { 
  AnimalMeasurementCreateRoute,
  AnimalMeasurementGetRoute,
  AnimalMeasurementListRoute,
  AnimalMeasurementUpdateRoute
} from "../../types/animal-measurement-types";
import { decodeId } from "../../utils/id-hash-util";

export async function createAnimalMeasurement(
  request: FastifyRequest<AnimalMeasurementCreateRoute>,
  reply: FastifyReply
): Promise<FastifyReply> {
  const { farmId, animalId } = request.params;
  const { measurementType, value, unit, measuredAt, method, notes } = request.body;
  
  // Decode IDs
  const decodedFarmId = decodeId(farmId);
  const decodedAnimalId = decodeId(animalId);
  
  // Verify animal belongs to farm
  const animal = await Animal.findOne({
    where: {
      id: decodedAnimalId,
      farmId: decodedFarmId,
    },
  });
  
  if (!animal) {
    return reply.status(404).send({
      error: "Animal not found",
    });
  }
  
  // Validate measurement date not in future
  const measurementDate = measuredAt ? new Date(measuredAt) : new Date();
  if (measurementDate > new Date()) {
    return reply.status(400).send({
      error: "Measurement date cannot be in the future",
    });
  }
  
  // Create measurement
  const measurement = await AnimalMeasurement.create({
    animalId: decodedAnimalId!,
    measurementType,
    value,
    unit,
    measuredAt: measurementDate,
    measuredBy: request!.user!.id,
    method,
    notes,
  });
  
  return reply.status(201).send({
    data: serializeAnimalMeasurement(measurement, request.server),
  });
}

export async function listAnimalMeasurements(
  request: FastifyRequest<AnimalMeasurementListRoute>,
  reply: FastifyReply
): Promise<FastifyReply> {
  const { farmId, animalId } = request.params;
  const { measurementType, startDate, endDate, limit = 100 } = request.query;
  
  const decodedFarmId = decodeId(farmId);
  const decodedAnimalId = decodeId(animalId);
  
  // Verify animal belongs to farm
  const animal = await Animal.findOne({
    where: {
      id: decodedAnimalId,
      farmId: decodedFarmId,
    },
  });
  
  if (!animal) {
    return reply.status(404).send({
      error: "Animal not found",
    });
  }
  
  // Build where clause
  const where: any = { animalId: decodedAnimalId };
  
  if (measurementType) {
    where.measurementType = measurementType;
  }
  
  if (startDate || endDate) {
    where.measuredAt = {};
    if (startDate) where.measuredAt[Op.gte] = new Date(startDate);
    if (endDate) where.measuredAt[Op.lte] = new Date(endDate);
  }
  
  const measurements = await AnimalMeasurement.findAll({
    where,
    order: [["measuredAt", "DESC"]],
    limit: Math.min(limit, 1000),
  });
  
  return reply.send({
    data: measurements.map(m => serializeAnimalMeasurement(m, request.server)),
  });
}

export async function getAnimalMeasurement(
  request: FastifyRequest<AnimalMeasurementGetRoute>,
  reply: FastifyReply
): Promise<FastifyReply> {
  const { farmId, animalId, measurementId } = request.params;
  
  const decodedFarmId = decodeId(farmId);
  const decodedAnimalId = decodeId(animalId);
  const decodedMeasurementId = decodeId(measurementId);
  
  // Verify animal belongs to farm
  const animal = await Animal.findOne({
    where: {
      id: decodedAnimalId,
      farmId: decodedFarmId,
    },
  });
  
  if (!animal) {
    return reply.status(404).send({
      error: "Animal not found",
    });
  }
  
  // Find measurement
  const measurement = await AnimalMeasurement.findOne({
    where: {
      id: decodedMeasurementId,
      animalId: decodedAnimalId,
    },
  });
  
  if (!measurement) {
    return reply.status(404).send({
      error: "Measurement not found",
    });
  }
  
  return reply.send({
    data: serializeAnimalMeasurement(measurement, request.server),
  });
}

export async function updateAnimalMeasurement(
  request: FastifyRequest<AnimalMeasurementUpdateRoute>,
  reply: FastifyReply
): Promise<FastifyReply> {
  const { farmId, animalId, measurementId } = request.params;
  const { value, unit, measuredAt, method, notes } = request.body;
  
  const decodedFarmId = decodeId(farmId);
  const decodedAnimalId = decodeId(animalId);
  const decodedMeasurementId = decodeId(measurementId);
  
  // Verify animal belongs to farm
  const animal = await Animal.findOne({
    where: {
      id: decodedAnimalId,
      farmId: decodedFarmId,
    },
  });
  
  if (!animal) {
    return reply.status(404).send({
      error: "Animal not found",
    });
  }
  
  // Find measurement
  const measurement = await AnimalMeasurement.findOne({
    where: {
      id: decodedMeasurementId,
      animalId: decodedAnimalId,
    },
  });
  
  if (!measurement) {
    return reply.status(404).send({
      error: "Measurement not found",
    });
  }
  
  // Validate measurement date not in future
  if (measuredAt) {
    const measurementDate = new Date(measuredAt);
    if (measurementDate > new Date()) {
      return reply.status(400).send({
        error: "Measurement date cannot be in the future",
      });
    }
    measurement.set("measuredAt", measurementDate);
  }
  
  // Update fields
  if (value !== undefined) measurement.set("value", value);
  if (unit !== undefined) measurement.set("unit", unit);
  if (method !== undefined) measurement.set("method", method);
  if (notes !== undefined) measurement.set("notes", notes);
  
  await measurement.save();
  
  return reply.send({
    data: serializeAnimalMeasurement(measurement, request.server),
  });
}