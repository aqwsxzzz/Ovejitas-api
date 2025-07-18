
import { Static, Type } from '@sinclair/typebox';
import { UserRole } from './user.model';
import { UserLanguage } from '../../models/user-model';
import { createGetEndpointSchema, createPostEndpointSchema } from '../../utils/schema-builder';

export const UserSchema = Type.Object({
	id: Type.Integer({ minimum: 1 }),
	displayName: Type.String({ minLength: 1 }),
	email: Type.String({ format: 'email' }),
	password: Type.String({ minLength: 8 }),
	isActive: Type.Boolean(),
	role: Type.Enum(UserRole),
	language: Type.Enum(UserLanguage),
	createdAt: Type.String({ format: 'date-time' }),
	updatedAt: Type.String({ format: 'date-time' }),
	lastVisitedFarmId: Type.Optional(Type.Integer({ minimun: 1 })),
}, {
	$id: 'user',
	additionalProperties: false,
});
const UserParamsSchema = Type.Object({
	id: Type.String(),
}, {
	$id: 'userParams',
	additionalProperties: false,
});

const UserCreateSchema = Type.Omit(UserSchema, ['id', 'createdAt', 'updatedAt', 'lastVisitedFarmId', 'role', 'language', 'isActive'], {
	$id: 'userCreate',
	additionalProperties: false,
});

const UserUpdateSchema = Type.Pick(UserSchema, ['displayName'], {
	$id: 'userUpdate',
	additionalProperties: false,
});
const UserResponseSchema = Type.Object({
	...UserSchema.properties,
	id: Type.String(),
	password: Type.Optional(Type.String()), // Password is not returned in responses
	lastVisitedFarmId: Type.Optional(Type.String()), // Encoded ID for last visited farm
}, {
	$id: 'userResponse',
	additionalProperties: false,
});

export type User = Static<typeof UserSchema>;
export type UserCreateInput = Static<typeof UserCreateSchema>;
export type UserUpdateInput = Static<typeof UserUpdateSchema>;
export type UserResponse = Static<typeof UserResponseSchema>;
export type UserParamsSchema = Static<typeof UserParamsSchema>;

export const userSchemas = [UserCreateSchema, UserUpdateSchema,  UserResponseSchema];

export const createUserSchema = createPostEndpointSchema({
	body: UserCreateSchema,
	dataSchema: UserResponseSchema,
	errorCodes: [400, 409],
});

export const updateUserSchema = createPostEndpointSchema({
	params: UserParamsSchema,
	body: UserUpdateSchema,
	dataSchema: UserResponseSchema,
	errorCodes: [400, 404],
});

export const getUserSchema = createGetEndpointSchema({
	params: UserParamsSchema,
	dataSchema: UserResponseSchema,
	errorCodes: [404],
});
