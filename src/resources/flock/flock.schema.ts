import { Static, Type } from '@sinclair/typebox';
import {
	createGetEndpointSchema,
	createListEndpointSchema,
	createPostEndpointSchema,
	createUpdateEndpointSchema,
	createDeleteEndpointSchema,
} from '../../utils/schema-builder';
import { PaginationQueryProps } from '../../utils/pagination';
import { SpeciesResponseSchema } from '../species/species.schema';
import { BreedResponseSchema } from '../breed/breed.schema';
import { UserLanguage } from '../user/user.schema';
import { FlockModel } from './flock.model';
import { SpeciesModel } from '../species/species.model';
import { SpeciesTranslationModel } from '../species-translation/species-translation.model';
import { BreedModel } from '../breed/breed.model';
import { BreedTranslationModel } from '../breed-translation/breed-translation.model';

export enum FlockType {
	Layers = 'layers',
	Broilers = 'broilers',
	DualPurpose = 'dual_purpose',
	General = 'general',
}

export enum FlockStatus {
	Active = 'active',
	Sold = 'sold',
	Culled = 'culled',
	Completed = 'completed',
}

export enum FlockAcquisitionType {
	Hatched = 'hatched',
	Purchased = 'purchased',
	Other = 'other',
}

export type FlockWithPossibleIncludes = FlockModel & {
	species?: SpeciesModel & {
		translations?: SpeciesTranslationModel[];
	};
	breed?: BreedModel & {
		translations?: BreedTranslationModel[];
	};
};

const FlockSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	farmId: Type.Integer(),
	speciesId: Type.Integer(),
	breedId: Type.Integer(),
	name: Type.String(),
	flockType: Type.Enum(FlockType),
	initialCount: Type.Integer(),
	currentCount: Type.Integer(),
	status: Type.Enum(FlockStatus),
	startDate: Type.String(),
	endDate: Type.Optional(Type.Union([Type.String(), Type.Null()])),
	houseName: Type.Optional(Type.Union([Type.String(), Type.Null()])),
	acquisitionType: Type.Enum(FlockAcquisitionType),
	ageAtAcquisitionWeeks: Type.Optional(Type.Union([Type.Integer(), Type.Null()])),
	notes: Type.Optional(Type.Union([Type.String(), Type.Null()])),
	createdAt: Type.String(),
	updatedAt: Type.String(),
}, {
	$id: 'flock',
	additionalProperties: false,
});

export const FlockCreateSchema = Type.Object({
	name: Type.String({ minLength: 1 }),
	speciesId: Type.String(),
	breedId: Type.String(),
	flockType: Type.Enum(FlockType),
	initialCount: Type.Integer({ minimum: 1 }),
	startDate: Type.String(),
	acquisitionType: Type.Enum(FlockAcquisitionType),
	endDate: Type.Optional(Type.String()),
	houseName: Type.Optional(Type.String()),
	ageAtAcquisitionWeeks: Type.Optional(Type.Integer({ minimum: 0 })),
	notes: Type.Optional(Type.String()),
	language: Type.Enum(UserLanguage),
}, {
	$id: 'flockCreate',
	additionalProperties: false,
});

export const FlockUpdateSchema = Type.Object({
	name: Type.Optional(Type.String({ minLength: 1 })),
	flockType: Type.Optional(Type.Enum(FlockType)),
	status: Type.Optional(Type.Enum(FlockStatus)),
	endDate: Type.Optional(Type.String()),
	houseName: Type.Optional(Type.String()),
	notes: Type.Optional(Type.String()),
}, {
	$id: 'flockUpdate',
	additionalProperties: false,
});

export const FlockResponseSchema = Type.Object({
	...FlockSchema.properties,
	id: Type.String(),
	farmId: Type.String(),
	speciesId: Type.String(),
	breedId: Type.String(),
	species: Type.Optional(SpeciesResponseSchema),
	breed: Type.Optional(BreedResponseSchema),
}, {
	$id: 'flockResponse',
	additionalProperties: false,
});

export const FlockIncludeSchema = Type.Object({
	include: Type.Optional(Type.String()),
	language: Type.Enum(UserLanguage),
	status: Type.Optional(Type.Enum(FlockStatus)),
	flockType: Type.Optional(Type.Enum(FlockType)),
	speciesId: Type.Optional(Type.String()),
	...PaginationQueryProps,
});

export const FlockParamsSchema = Type.Object({
	id: Type.String(),
});

export type Flock = Static<typeof FlockSchema>;
export type FlockCreate = Static<typeof FlockCreateSchema>;
export type FlockUpdate = Static<typeof FlockUpdateSchema>;
export type FlockResponse = Static<typeof FlockResponseSchema>;
export type FlockInclude = Static<typeof FlockIncludeSchema>;
export type FlockParams = Static<typeof FlockParamsSchema>;

export const createFlockSchema = createPostEndpointSchema({
	body: FlockCreateSchema,
	dataSchema: FlockResponseSchema,
	errorCodes: [400, 409],
});

export const listFlockSchema = createListEndpointSchema({
	querystring: FlockIncludeSchema,
	dataSchema: Type.Array(FlockResponseSchema),
	errorCodes: [404],
});

export const getFlockByIdSchema = createGetEndpointSchema({
	params: FlockParamsSchema,
	querystring: FlockIncludeSchema,
	dataSchema: FlockResponseSchema,
	errorCodes: [404],
});

export const updateFlockSchema = createUpdateEndpointSchema({
	params: FlockParamsSchema,
	body: FlockUpdateSchema,
	dataSchema: FlockResponseSchema,
	errorCodes: [400, 404],
});

export const deleteFlockSchema = createDeleteEndpointSchema({
	params: FlockParamsSchema,
	errorCodes: [400, 404],
});
