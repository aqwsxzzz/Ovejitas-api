import { Static, Type } from '@sinclair/typebox';
import { createGetEndpointSchema, createPostEndpointSchema } from '../../utils/schema-builder';
import { FarmMemberRole } from '../farm-member/farm-member.schema';

export enum InvitationStatus {
	PENDING = 'pending',
	ACCEPTED = 'accepted',
	EXPIRED = 'expired',
	CANCELLED = 'cancelled',
}

export const InvitationSchema = Type.Object({
	id: Type.Integer(),
	email: Type.String({ format: 'email' }),
	farmId: Type.Integer(),
	role: Type.Enum(FarmMemberRole, { default: FarmMemberRole.MEMBER }),
	token: Type.String(),
	status: Type.Enum(InvitationStatus, { default: InvitationStatus.PENDING }),
	createdAt: Type.String({ format: 'date-time' }),
	updatedAt: Type.String({ format: 'date-time' }),
	expiresAt: Type.String({ format: 'date-time' }),
}, {
	$id: 'invitation',
	additionalProperties: false,
});

const InvitationCreateSchema = Type.Object({
	email: Type.String({ format: 'email' }),
	farmId: Type.String(),
}, {
	$id: 'invitationCreate',
	additionalProperties: false,
});

const InvitationAcceptSchema = Type.Object({
	token: Type.String(),
	email: Type.String({ format: 'email' }),
}, {
	$id: 'invitationAccept',
	additionalProperties: false,
});

const InvitationResponseSchema = Type.Object({
	...InvitationSchema.properties,
	id: Type.String(),
	farmId: Type.String(),
});

const ListInvitationParamsSchema = Type.Object({
	farmId: Type.String(),
	status: Type.Optional(Type.Enum(InvitationStatus)),
	email: Type.Optional(Type.String()),
});

export type Invitation = Static<typeof InvitationSchema>;
export type InvitationCreateInput = Static<typeof InvitationCreateSchema>;
export type InvitationAcceptInput = Static<typeof InvitationAcceptSchema>;
export type InvitationResponse = Static<typeof InvitationResponseSchema>;
export type ListInvitationParams = Static<typeof ListInvitationParamsSchema>;

export const createInvitationSchema = createPostEndpointSchema({
	body: InvitationCreateSchema,
	dataSchema: InvitationResponseSchema,
});

export const acceptInvitationSchema = createPostEndpointSchema({
	body: InvitationAcceptSchema,
	dataSchema: InvitationResponseSchema,
	errorCodes: [400, 404],
});

export const listInvitationsSchema = createGetEndpointSchema({
	querystring: ListInvitationParamsSchema,
	dataSchema: Type.Array(InvitationResponseSchema),
	errorCodes: [400, 404],
});
