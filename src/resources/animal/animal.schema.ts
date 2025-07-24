import { Static, Type } from '@sinclair/typebox';
import { createPostEndpointSchema } from '../../utils/schema-builder';

export enum AnimalSex {
	Male = 'male',
	Female = 'female',
	Unknown = 'unknown',
}

export enum AnimalStatus {
	Alive = 'alive',
	Sold = 'sold',
	Deceased = 'deceased',
}

export enum AnimalReproductiveStatus {
	Open = 'open',
	Pregnant = 'pregnant',
	Lactating = 'lactating',
	Other = 'other',
}

export enum AnimalAcquisitionType {
	Born = 'born',
	Purchased = 'purchased',
	Other = 'other',
}

const AnimalSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	farmId: Type.Integer(),
	speciesId: Type.Integer(),
	breedId: Type.Integer(),
	name: Type.String(),
	tagNumber: Type.String(),
	sex: Type.Enum(AnimalSex),
	birthDate: Type.String(),
	weight: Type.Number(),
	status: Type.Enum(AnimalStatus),
	reproductiveStatus: Type.Enum(AnimalReproductiveStatus),
	fatherId: Type.Integer(),
	motherId: Type.Integer(),
	acquisitionType: Type.Enum(AnimalAcquisitionType),
	acquisitionDate: Type.String(),
	createdAt: Type.String(),
	updatedAt: Type.String(),
}, {
	$id: 'animal',
	additionalProperties: false,
});

export const AnimalCreateSchema = Type.Object({
	name: Type.String(),
	speciesId: Type.String(),
	breedId: Type.String(),
	tagNumber: Type.String(),
	sex: Type.Optional(Type.Enum(AnimalSex)),
	birthDate: Type.Optional(Type.String()),
	weight: Type.Optional(Type.Number()),
	status: Type.Optional(Type.Enum(AnimalStatus)),
	reproductiveStatus: Type.Optional(Type.Enum(AnimalReproductiveStatus)),
	fatherId: Type.Optional(Type.String()),
	motherId: Type.Optional(Type.String()),
	acquisitionType: Type.Optional(Type.Enum(AnimalAcquisitionType)),
	acquisitionDate: Type.Optional(Type.String()),
}, {
	$id: 'animalCreate',
	additionalProperties: false,
});

export const AnimalUpdateSchema = Type.Object({
	name: Type.String(),
	speciesId: Type.String(),
	breedId: Type.String(),
	tagNumber: Type.String(),
	sex: Type.String(),
	birthDate: Type.String(),
	weight: Type.Number(),
	status: Type.String(),
	reproductiveStatus: Type.String(),
	fatherId: Type.String(),
	motherId: Type.String(),
	acquisitionType: Type.String(),
	acquisitionDate: Type.String(),
}, {
	$id: 'animalUpdate',
	additionalProperties: false,
});

export const AnimalResponseSchema = Type.Object({
	...AnimalSchema.properties,
	id: Type.String(),
	speciesId: Type.String(),
	breedId: Type.String(),
	weight: Type.Optional(Type.Number()),
	fatherId: Type.Optional(Type.String()),
	motherId: Type.Optional(Type.String()),

}, {
	$id: 'animalResponse',
	additionalProperties: false,
},
);

export const AnimalParamsSchema = Type.Object({
	id: Type.String(),
});

export type Animal = Static<typeof AnimalSchema>;
export type AnimalCreate = Static<typeof AnimalCreateSchema>;
export type AnimalResponse = Static<typeof AnimalResponseSchema>;
export type AnimalUpdate = Static<typeof AnimalUpdateSchema>;
export type AnimalParams = Static<typeof AnimalParamsSchema>;

export const animalSchemas = [AnimalSchema, AnimalCreateSchema, AnimalUpdateSchema, AnimalResponseSchema];

export const createAnimalSchema = createPostEndpointSchema({
	body: AnimalCreateSchema,
	dataSchema: AnimalResponseSchema,
	errorCodes: [400, 409],
});
