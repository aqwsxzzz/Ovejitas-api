import { SpeciesResponse, SpeciesResponseSchema } from './../species/species.schema';
import { Static, Type } from '@sinclair/typebox';
import { createGetEndpointSchema, createPostEndpointSchema } from '../../utils/schema-builder';
import { BreedResponse, BreedResponseSchema } from '../breed/breed.schema';
import { AnimalMeasurementResponse, AnimalMeasurementResponseSchema } from '../animal-measurement/animal-measurement.schema';
import { AnimalModel } from './animal.model';
import { SpeciesModel } from '../species/species.model';
import { SpeciesTranslationModel } from '../species-translation/species-translation.model';
import { BreedModel } from '../breed/breed.model';
import { AnimalMeasurementModel } from '../animal-measurement/animal-measurement.model';
import { UserLanguage } from '../user/user.schema';

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

export type AnimalWithPossibleIncludes = AnimalModel & {
	species?: SpeciesModel & {
		translations?: SpeciesTranslationModel[];
	};
	breed?: BreedModel;
	father?: AnimalModel;
	mother?: AnimalModel;
	measurements?: AnimalMeasurementModel[];
};

export type AnimalWithIncludes = AnimalResponse & {
    species?: SpeciesResponse;
    breed?: BreedResponse;
    father?: Partial<AnimalResponse>;
    mother?: Partial<AnimalResponse>;
    lastMeasurement?: AnimalMeasurementResponse;
};

const AnimalSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	farmId: Type.Integer(),
	speciesId: Type.Integer(),
	breedId: Type.Integer(),
	weightId: Type.Integer(),
	name: Type.String(),
	tagNumber: Type.String(),
	sex: Type.Enum(AnimalSex),
	birthDate: Type.String(),
	status: Type.Enum(AnimalStatus),
	reproductiveStatus: Type.Enum(AnimalReproductiveStatus),
	fatherId: Type.Integer(),
	motherId: Type.Integer(),
	acquisitionType: Type.Enum(AnimalAcquisitionType),
	acquisitionDate: Type.String(),
	createdAt: Type.String(),
	updatedAt: Type.String(),
	groupName: Type.String(),
}, {
	$id: 'animal',
	additionalProperties: false,
});

export const AnimalCreateSchema = Type.Object({
	name: Type.Optional(Type.String()),
	speciesId: Type.String(),
	breedId: Type.String(),
	tagNumber: Type.String(),
	sex: Type.Optional(Type.Enum(AnimalSex)),
	birthDate: Type.Optional(Type.String()),
	status: Type.Optional(Type.Enum(AnimalStatus)),
	reproductiveStatus: Type.Optional(Type.Enum(AnimalReproductiveStatus)),
	fatherId: Type.Optional(Type.String()),
	motherId: Type.Optional(Type.String()),
	acquisitionType: Type.Optional(Type.Enum(AnimalAcquisitionType)),
	acquisitionDate: Type.Optional(Type.String()),
	groupName: Type.Optional(Type.String()),
}, {
	$id: 'animalCreate',
	additionalProperties: false,
});

export const AnimalUpdateSchema = Type.Object({
	name: Type.Optional(Type.String()),
	speciesId: Type.String(),
	breedId: Type.String(),
	tagNumber: Type.String(),
	sex: Type.Optional(Type.Enum(AnimalSex)),
	birthDate: Type.Optional(Type.String()),
	status: Type.Optional(Type.Enum(AnimalStatus)),
	reproductiveStatus: Type.Optional(Type.Enum(AnimalReproductiveStatus)),
	fatherId: Type.Optional(Type.String()),
	motherId: Type.Optional(Type.String()),
	acquisitionType: Type.Optional(Type.Enum(AnimalAcquisitionType)),
	acquisitionDate: Type.Optional(Type.String()),
	groupName: Type.Optional(Type.String()),
}, {
	$id: 'animalUpdate',
	additionalProperties: false,
});

export const AnimalBulkCreateSchema = Type.Object({
	speciesId: Type.String(),
	breedId: Type.String(),
	groupName: Type.Optional(Type.String()),
	tags: Type.Optional(Type.Array(Type.String())),
	tagPrefix: Type.Optional(Type.String()),
	tagStartNumber: Type.Optional(Type.Integer({ minimum: 1 })),
	count: Type.Optional(Type.Integer({ minimum: 1, maximum: 100 })),
}, {
	$id: 'animalBulkCreate',
	additionalProperties: false,
});

const ParentAnimalSchema = Type.Object({
	id: Type.String(),
	name: Type.String(),
	tagNumber: Type.String(),
	createdAt: Type.String(),
	updatedAt: Type.String(),
}, {
	additionalProperties: false,
});

export const AnimalResponseSchema = Type.Object({
	...AnimalSchema.properties,
	id: Type.String(),
	speciesId: Type.String(),
	breedId: Type.String(),
	fatherId: Type.Optional(Type.String()),
	motherId: Type.Optional(Type.String()),
	weightId: Type.Optional(Type.String()),
	species: Type.Optional(SpeciesResponseSchema),
	breed: Type.Optional(BreedResponseSchema),
	father: Type.Optional(ParentAnimalSchema),
	mother: Type.Optional(ParentAnimalSchema),
	lastMeasurement: Type.Optional(AnimalMeasurementResponseSchema),
	farmId: Type.String(),
}, {
	$id: 'animalResponse',
	additionalProperties: false,
},
);

export const AnimalIncludeSchema = Type.Object({
	include: Type.Optional(Type.String()),
	language: Type.Enum(UserLanguage),
	sex: Type.Optional(Type.Enum(AnimalSex)),
});

export const AnimalParamsSchema = Type.Object({
	id: Type.String(),
});

export type Animal = Static<typeof AnimalSchema>;
export type AnimalCreate = Static<typeof AnimalCreateSchema>;
export type AnimalResponse = Static<typeof AnimalResponseSchema>;
export type AnimalUpdate = Static<typeof AnimalUpdateSchema>;
export type AnimalParams = Static<typeof AnimalParamsSchema>;
export type AnimalInclude = Static<typeof AnimalIncludeSchema>;
export type AnimalBulkCreate = Static<typeof AnimalBulkCreateSchema>;

export const createAnimalSchema = createPostEndpointSchema({
	body: AnimalCreateSchema,
	dataSchema: AnimalResponseSchema,
	errorCodes: [400, 409],
});

export const listAnimalSchema = createGetEndpointSchema({
	querystring: AnimalIncludeSchema,
	dataSchema: Type.Array(AnimalResponseSchema),
	errorCodes: [404],
});

export const getAnimalByIdSchema = createGetEndpointSchema({
	params: AnimalParamsSchema,
	querystring: AnimalIncludeSchema,
	dataSchema: AnimalResponseSchema,
	errorCodes: [404],
});

export const AnimalBulkCreateResponseSchema = Type.Object({
	created: Type.Array(AnimalResponseSchema),
	failed: Type.Array(Type.Object({
		tagNumber: Type.String(),
		reason: Type.String(),
	})),
}, {
	$id: 'animalBulkCreateResponse',
	additionalProperties: false,
});

export type AnimalBulkCreateResponse = Static<typeof AnimalBulkCreateResponseSchema>;

export const bulkCreateAnimalSchema = createPostEndpointSchema({
	body: AnimalBulkCreateSchema,
	dataSchema: AnimalBulkCreateResponseSchema,
	errorCodes: [400, 409],
});

// Dashboard schemas
export const AnimalDashboardItemSchema = Type.Object({
	count: Type.Integer(),
	species: Type.Object({
		id: Type.String(),
		name: Type.String(),
	}),
}, {
	$id: 'animalDashboardItem',
	additionalProperties: false,
});

export const AnimalDashboardResponseSchema = Type.Array(AnimalDashboardItemSchema, {
	$id: 'animalDashboardResponse',
});

export type AnimalDashboardItem = Static<typeof AnimalDashboardItemSchema>;
export type AnimalDashboardResponse = Static<typeof AnimalDashboardResponseSchema>;

export const getAnimalDashboardSchema = createGetEndpointSchema({
	dataSchema: AnimalDashboardResponseSchema,
	errorCodes: [400, 404],
});
