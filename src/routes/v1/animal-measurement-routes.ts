import { FastifyInstance } from "fastify";
import {
  createAnimalMeasurement,
  listAnimalMeasurements,
  getAnimalMeasurement,
  updateAnimalMeasurement,
} from "../../controllers/v1/animal-measurement-controller";
import {
  animalMeasurementCreateSchema,
  animalMeasurementUpdateSchema,
  animalMeasurementListSchema,
  animalMeasurementGetSchema,
} from "../../schemas/animal-measurement-schema";
import { animalMeasurementResponseSchema } from "../../serializers/animal-measurement-serializer";

export default async function animalMeasurementRoutes(
  fastify: FastifyInstance
): Promise<void> {
  // List measurements for an animal
  fastify.get(
    "/farms/:farmId/animals/:animalId/measurements",
    {
      preValidation: [fastify.authenticate],
      schema: {
        ...animalMeasurementListSchema,
        response: {
          200: {
            type: "object",
            properties: {
              data: {
                type: "array",
                items: animalMeasurementResponseSchema,
              },
            },
            required: ["data"],
          },
          404: {
            type: "object",
            properties: {
              error: { type: "string" },
            },
            required: ["error"],
          },
        },
      },
    },
    listAnimalMeasurements
  );

  // Create new measurement
  fastify.post(
    "/farms/:farmId/animals/:animalId/measurements",
    {
      preValidation: [fastify.authenticate],
      schema: {
        ...animalMeasurementCreateSchema,
        response: {
          201: {
            type: "object",
            properties: {
              data: animalMeasurementResponseSchema,
            },
            required: ["data"],
          },
          400: {
            type: "object",
            properties: {
              error: { type: "string" },
            },
            required: ["error"],
          },
          404: {
            type: "object",
            properties: {
              error: { type: "string" },
            },
            required: ["error"],
          },
        },
      },
    },
    createAnimalMeasurement
  );

  // Get specific measurement
  fastify.get(
    "/farms/:farmId/animals/:animalId/measurements/:measurementId",
    {
      preValidation: [fastify.authenticate],
      schema: {
        ...animalMeasurementGetSchema,
        response: {
          200: {
            type: "object",
            properties: {
              data: animalMeasurementResponseSchema,
            },
            required: ["data"],
          },
          404: {
            type: "object",
            properties: {
              error: { type: "string" },
            },
            required: ["error"],
          },
        },
      },
    },
    getAnimalMeasurement
  );

  // Update specific measurement
  fastify.put(
    "/farms/:farmId/animals/:animalId/measurements/:measurementId",
    {
      preValidation: [fastify.authenticate],
      schema: {
        ...animalMeasurementUpdateSchema,
        response: {
          200: {
            type: "object",
            properties: {
              data: animalMeasurementResponseSchema,
            },
            required: ["data"],
          },
          400: {
            type: "object",
            properties: {
              error: { type: "string" },
            },
            required: ["error"],
          },
          404: {
            type: "object",
            properties: {
              error: { type: "string" },
            },
            required: ["error"],
          },
        },
      },
    },
    updateAnimalMeasurement
  );
}