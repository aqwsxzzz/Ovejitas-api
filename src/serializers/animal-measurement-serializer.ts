import { AnimalMeasurement } from "../models/animal-measurement-model";
import { FastifyInstance } from "fastify";
import { encodeId } from "../utils/id-hash-util";

export const animalMeasurementResponseSchema = {
  type: "object",
  properties: {
    id: { type: "string" },
    animalId: { type: "string" },
    measurementType: { type: "string" },
    value: { type: "number" },
    unit: { type: "string" },
    measuredAt: { type: "string", format: "date-time" },
    measuredBy: { type: ["string", "null"] },
    method: { type: ["string", "null"] },
    notes: { type: ["string", "null"] },
    createdAt: { type: "string", format: "date-time" },
    updatedAt: { type: "string", format: "date-time" },
  },
  required: [
    "id", 
    "animalId", 
    "measurementType", 
    "value", 
    "unit", 
    "measuredAt", 
    "createdAt", 
    "updatedAt"
  ],
  additionalProperties: false,
};

export function serializeAnimalMeasurement(
  measurement: AnimalMeasurement, 
  server: FastifyInstance
) {
  return {
    id: encodeId(measurement.id),
    animalId: encodeId(measurement.animalId),
    measurementType: measurement.measurementType,
    value: parseFloat(measurement.value.toString()),
    unit: measurement.unit,
    measuredAt: measurement.measuredAt.toISOString(),
    measuredBy: measurement.measuredBy ? encodeId(measurement.measuredBy) : null,
    method: measurement.method || null,
    notes: measurement.notes || null,
    createdAt: measurement.createdAt.toISOString(),
    updatedAt: measurement.updatedAt.toISOString(),
  };
}