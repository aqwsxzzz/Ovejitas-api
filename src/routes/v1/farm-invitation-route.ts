import { FastifyInstance } from "fastify";
import * as invitationController from "../../controllers/v1/farm-invitation-controller";
import { farmInvitationCreateSchema, farmInvitationAcceptSchema, farmInvitationErrorResponseSchema } from "../../schemas/farm-invitation-schema";
import { farmInvitationResponseSchema } from "../../serializers/farm-invitation-serializer";

export default async function farmInvitationRoutes(fastify: FastifyInstance) {
	fastify.post(
		"/farms/:farmId/invitations",
		{
			schema: {
				params: farmInvitationCreateSchema.params,
				body: farmInvitationCreateSchema.body,
				response: { 201: farmInvitationResponseSchema, 400: farmInvitationErrorResponseSchema },
			},
		},
		invitationController.sendInvitation
	);

	fastify.post(
		"/invitations/accept",
		{
			schema: {
				body: farmInvitationAcceptSchema.body,
				response: { 200: { type: "object", properties: { message: { type: "string" } }, required: ["message"] }, 400: farmInvitationErrorResponseSchema },
			},
		},
		invitationController.acceptInvitation
	);

	fastify.get(
		"/farms/:farmId/invitations",
		{
			schema: {
				params: farmInvitationCreateSchema.params,
				response: { 200: { type: "array", items: farmInvitationResponseSchema }, 400: farmInvitationErrorResponseSchema },
			},
		},
		invitationController.listInvitations
	);

	fastify.delete(
		"/invitations/:invitationId",
		{
			schema: {
				params: { type: "object", properties: { invitationId: { type: "string" } }, required: ["invitationId"] },
				response: { 200: { type: "object", properties: { message: { type: "string" } }, required: ["message"] }, 404: farmInvitationErrorResponseSchema },
			},
		},
		invitationController.cancelInvitation
	);
}
