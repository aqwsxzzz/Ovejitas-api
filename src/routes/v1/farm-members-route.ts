import { FastifyInstance } from "fastify";
import { createFarmMember, getFarmMemberById, updateFarmMember, deleteFarmMember, getFarmMembersByFarmId } from "../../controllers/v1/farm-members-controller";
import { farmMembersCreateSchema, farmMembersUpdateSchema, farmMembersIdParamSchema, farmMembersFarmIdParamSchema, farmMembersFarmIdAndMemberIdParamSchema } from "../../schemas/farm-members-schema";
import { farmMembersResponseSchema, farmMembersArrayResponseSchema } from "../../serializers/farm-members-serializer";

export default async function farmMembersRoutes(fastify: FastifyInstance) {
	fastify.post(
		"/farms/:farmId/members",
		{
			schema: {
				...farmMembersCreateSchema,
				response: { 201: farmMembersResponseSchema },
			},
		},
		createFarmMember
	);

	fastify.get(
		"/farms/:farmId/members",
		{
			schema: {
				...farmMembersFarmIdParamSchema,
				response: { 200: farmMembersArrayResponseSchema },
			},
		},
		getFarmMembersByFarmId
	);

	fastify.get(
		"/farms/:farmId/members/:memberId",
		{
			schema: {
				...farmMembersFarmIdAndMemberIdParamSchema,
				response: { 200: farmMembersResponseSchema },
			},
		},
		getFarmMemberById
	);

	fastify.patch(
		"/farms/:farmId/members/:memberId",
		{
			schema: {
				...farmMembersFarmIdAndMemberIdParamSchema,
				body: farmMembersUpdateSchema.body,
				response: { 200: farmMembersResponseSchema },
			},
		},
		updateFarmMember
	);

	fastify.delete(
		"/farms/:farmId/members/:memberId",
		{
			schema: {
				...farmMembersFarmIdAndMemberIdParamSchema,
				response: { 200: { type: "object", properties: { message: { type: "string" } }, required: ["message"] } },
			},
		},
		deleteFarmMember
	);
}
