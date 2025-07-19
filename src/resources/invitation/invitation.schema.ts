import { Static, Type } from '@sinclair/typebox';
import { FarmMemberRole } from '../farm-member/farm-member.model';
import { FarmInvitationStatus } from './invitation.model';
import { createPostEndpointSchema } from '../../utils/schema-builder';

export const InvitationSchema = Type.Object({
	id: Type.Integer(),
	email: Type.String({ format: 'email' }),
	farmId: Type.Integer(),
	role: Type.Enum(FarmMemberRole, { default: FarmMemberRole.MEMBER }),
	token: Type.String(),
	status: Type.Enum(FarmInvitationStatus, { default: FarmInvitationStatus.PENDING }),
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

const InvitationResponseSchema = Type.Object({
	...InvitationSchema.properties,
	id: Type.String(),
	farmId: Type.String(),
});

export type Invitation = Static<typeof InvitationSchema>;
export type InvitationCreateInput = Static<typeof InvitationCreateSchema>;
export type InvitationResponse = Static<typeof InvitationResponseSchema>;

export const invitationSchemas = [InvitationCreateSchema];

export const createInvitationSchema = createPostEndpointSchema({
	body: InvitationCreateSchema,
	dataSchema: InvitationResponseSchema,
});
