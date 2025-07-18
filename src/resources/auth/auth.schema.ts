import { Static, Type } from '@sinclair/typebox';
import { UserSchema } from '../user/user.schema';
import { createGetEndpointSchema, createPostEndpointSchema } from '../../utils/schema-builder';

const UserLoginSchema = Type.Pick(UserSchema, ['email', 'password'], {
	$id: 'userLogin',
	additionalProperties: false,
});

const UserResponseSchema = Type.Omit(UserSchema, ['password'], {
	$id: 'userResponse',
	additionalProperties: false,
});

export type UserLoginInput = Static<typeof UserLoginSchema>;

export const authSchemas = [UserLoginSchema];

export const loginUserSchema = createPostEndpointSchema({
	body: UserLoginSchema,
	dataSchema: UserResponseSchema,
	errorCodes: [400,  404],
});

export const currentUserSchema = createGetEndpointSchema({
	dataSchema: UserResponseSchema,
	errorCodes: [400, 404],
});
