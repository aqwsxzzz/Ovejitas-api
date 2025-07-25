import { Static, Type } from '@sinclair/typebox';
import { createGetEndpointSchema } from '../../utils/schema-builder';

export enum AnimalMeasurementType {
	Weight = 'weight',
	Height = 'height',
	Temperature = 'temperature',
}

export enum AnimalMeasurementUnit {
    Kg = 'kg',
    Cms = 'cms',
    Celsius = 'celsius',
}

const AnimalMeasurementSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	animalId: Type.Integer(),
	measurementType: Type.Enum(AnimalMeasurementType),
	value: Type.Number(),
	unit: Type.Enum(AnimalMeasurementUnit),
	measuredAt: Type.String(),
	measuredBy: Type.String(),
	notes: Type.String(),
	createdAt: Type.String(),
	updatedAt: Type.String(),
},
{
	$id: 'animalMeasurement',
	additionalProperties: false,
});

const AnimalMeasurementResponseSchema = Type.Object({
	...AnimalMeasurementSchema.properties,
	animalId: Type.String(),
	measuredBy: Type.String(),
},
{
	$id: 'animalMeasurementResponse',
	additionalProperties: false,
});

const AnimalMeasurementParamsSchema = Type.Object({
	animalId: Type.String(),
});

export type AnimalMeasurement = Static<typeof AnimalMeasurementSchema>;
export type AnimalMeasurementResponse = Static<typeof AnimalMeasurementResponseSchema>;
export type AnimalMeasurementParams = Static<typeof AnimalMeasurementParamsSchema>;

export const listAnimalMeasurementsSchema = createGetEndpointSchema({
	querystring: AnimalMeasurementParamsSchema,
	dataSchema: Type.Array(AnimalMeasurementResponseSchema),
	errorCodes: [404],
});
