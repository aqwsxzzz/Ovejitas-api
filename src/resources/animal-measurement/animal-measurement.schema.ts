import { Static, Type } from '@sinclair/typebox';
import {
	createGetEndpointSchema,
	createPostEndpointSchema,
	createDeleteEndpointSchema,
} from '../../utils/schema-builder';

export enum AnimalMeasurementType {
	Weight = 'weight',
	Height = 'height',
	Temperature = 'temperature',
}

export enum AnimalMeasurementUnit {
	Kg = 'kg',
	Cm = 'cm',
	Celsius = 'celsius',
}

const AnimalMeasurementSchema = Type.Object(
	{
		id: Type.Integer({ minimum: 1 }),
		animalId: Type.Integer(),
		measurementType: Type.Enum(AnimalMeasurementType),
		value: Type.Number(),
		unit: Type.Enum(AnimalMeasurementUnit),
		measuredAt: Type.String(),
		measuredBy: Type.Integer(),
		notes: Type.Optional(Type.String()),
		createdAt: Type.String(),
		updatedAt: Type.String(),
	},
	{
		$id: 'animalMeasurement',
		additionalProperties: false,
	},
);

export const AnimalMeasurementResponseSchema = Type.Object(
	{
		...AnimalMeasurementSchema.properties,
		animalId: Type.String(),
		measuredBy: Type.String(),
		id: Type.String(),
	},
	{
		$id: 'animalMeasurementResponse',
		additionalProperties: false,
	},
);

const AnimalMeasurementParamsSchema = Type.Object({
	animalId: Type.String(),
});

const AnimalMeasurementDeleteParamsSchema = Type.Object({
	animalId: Type.String(),
	measurementId: Type.String(),
});

export type AnimalMeasurement = Static<typeof AnimalMeasurementSchema>;
export type AnimalMeasurementResponse = Static<typeof AnimalMeasurementResponseSchema>;
export type AnimalMeasurementParams = Static<typeof AnimalMeasurementParamsSchema>;
export type AnimalMeasurementDeleteParams = Static<typeof AnimalMeasurementDeleteParamsSchema>;
export type AnimalMeasurementCreate = Static<typeof AnimalMeasurementCreateSchema>;

const AnimalMeasurementCreateSchema = Type.Object(
	{
		measurementType: Type.Enum(AnimalMeasurementType),
		value: Type.Number({ minimum: 0 }),
		unit: Type.Enum(AnimalMeasurementUnit),
		measuredAt: Type.Optional(Type.String()),
		notes: Type.Optional(Type.String()),
	},
	{
		$id: 'animalMeasurementCreate',
		additionalProperties: false,
	},
);

export const listAnimalMeasurementsSchema = createGetEndpointSchema({
	params: AnimalMeasurementParamsSchema,
	dataSchema: Type.Array(AnimalMeasurementResponseSchema),
	errorCodes: [404],
});

export const createAnimalMeasurementSchema = createPostEndpointSchema({
	params: AnimalMeasurementParamsSchema,
	body: AnimalMeasurementCreateSchema,
	dataSchema: AnimalMeasurementResponseSchema,
	errorCodes: [400, 404],
});

export const deleteAnimalMeasurementSchema = createDeleteEndpointSchema({
	params: AnimalMeasurementDeleteParamsSchema,
	errorCodes: [404],
});
