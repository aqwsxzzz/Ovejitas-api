import { Static, Type } from '@sinclair/typebox';
import { FarmMemberModel  } from './farm-member.model';
import { createGetEndpointSchema, createPostEndpointSchema } from '../../utils/schema-builder';
import { FarmModel } from '../farm/farm.model';

export enum FarmMemberRole {
	OWNER = 'owner',
	MEMBER = 'member',
}

const FarmMemberSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	farmId: Type.Integer({ minimum: 1 }),
	userId: Type.Integer({ minimum: 1 }),
	role: Type.Enum(FarmMemberRole),
	createdAt: Type.String({ format: 'date-time' }),
	updatedAt: Type.String({ format: 'date-time' }),
}, {
	$id: 'farmMember',
	additionalProperties: false,
});

const FarmMemberParamsSchema = Type.Pick(FarmMemberSchema, ['id'], {
	$id: 'farmMemberParams',
	additionalProperties: false,
});

const FarmMemberCreateSchema = Type.Pick(FarmMemberSchema, ['farmId','userId','role'], {
	$id: 'farmMemberCreate',
	additionalProperties: false,
});

const FarmMemberUpdateSchema = Type.Pick(FarmMemberSchema, ['role'], {
	$id: 'farmMemberUpdate',
	additionalProperties: false,
});

const FarmMemberResponseSchema = Type.Object({
	...FarmMemberSchema.properties,
	id: Type.String(),
}, {
	$id: 'farmMemberResponse',
	additionalProperties: false,
});

export type FarmMember = Static<typeof FarmMemberSchema>;
export type FarmMemberCreateInput = Static<typeof FarmMemberCreateSchema>;
export type FarmMemberUpdateInput = Static<typeof FarmMemberUpdateSchema>;
export type FarmMemberResponse = Static<typeof FarmMemberResponseSchema>;
export type FarmMemberParamsSchema = Static<typeof FarmMemberParamsSchema>;

export interface FarmMemberWithFarm extends FarmMemberModel {
	farm: FarmModel;
}

export const farmMemberSchemas = [FarmMemberCreateSchema, FarmMemberUpdateSchema, FarmMemberResponseSchema];

export const createFarmMemberSchema = createPostEndpointSchema({
	body: FarmMemberCreateSchema,
	dataSchema: FarmMemberResponseSchema,
	errorCodes: [400, 409],
});

export const updateFarmMemberSchema = createPostEndpointSchema({
	params: FarmMemberParamsSchema,
	body: FarmMemberUpdateSchema,
	dataSchema: FarmMemberResponseSchema,
	errorCodes: [400, 404],
});

export const getFarmMemberSchema = createGetEndpointSchema({
	params: FarmMemberParamsSchema,
	dataSchema: FarmMemberResponseSchema,
	errorCodes: [404],
});
