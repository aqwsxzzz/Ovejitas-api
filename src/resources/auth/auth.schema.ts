import { Static, Type } from '@sinclair/typebox';
import { UserLanguage, UserSchema } from '../user/user.schema';
import { createGetEndpointSchema, createPostEndpointSchema } from '../../utils/schema-builder';

const UserLoginSchema = Type.Pick(UserSchema, ['email', 'password'], {
	$id: 'userLogin',
	additionalProperties: false,
});

const UserSignupSchema = Type.Object({
	email: Type.String({ format: 'email' }),
	password: Type.String({ minLength: 6 }),
	displayName: Type.String({ minLength: 2, maxLength: 100 }),
	language: Type.Optional(Type.Enum(UserLanguage)),
	invitationToken: Type.Optional(Type.String()),
}, {
	$id: 'userSignup',
	additionalProperties: false,
});

const UserResponseSchema = Type.Omit(UserSchema, ['password'], {
	$id: 'userResponse',
	additionalProperties: false,
});

export type UserLoginInput = Static<typeof UserLoginSchema>;
export type UserSignupInput = Static<typeof UserSignupSchema>;

export const authSchemas = [UserLoginSchema, UserSignupSchema];

export const loginUserSchema = createPostEndpointSchema({
	body: UserLoginSchema,
	dataSchema: UserResponseSchema,
	errorCodes: [400,  404],
});

export const signupUserSchema = createPostEndpointSchema({
	body: UserSignupSchema,
	dataSchema: UserResponseSchema,
	errorCodes: [400, 409],
});

export const currentUserSchema = createGetEndpointSchema({
	dataSchema: UserResponseSchema,
	errorCodes: [400, 404],
});
