import { FastifyInstance } from "fastify";
import { createFarmMember, getFarmMemberById, updateFarmMember, deleteFarmMember } from "../../controllers/v1/farm-members-controller";
import { farmMembersCreateSchema, farmMembersUpdateSchema, farmMembersIdParamSchema } from "../../schemas/farm-members-schema";
import { farmMembersResponseSchema } from "../../serializers/farm-members-serializer";

export default async function farmMembersRoutes(fastify: FastifyInstance) {
	fastify.post(
		"/farm-members",
		{
			schema: {
				...farmMembersCreateSchema,
				response: { 201: farmMembersResponseSchema },
			},
		},
		createFarmMember
	);

	fastify.get(
		"/farm-members/:id",
		{
			schema: {
				...farmMembersIdParamSchema,
				response: { 200: farmMembersResponseSchema },
			},
		},
		getFarmMemberById
	);

	fastify.patch(
		"/farm-members/:id",
		{
			schema: {
				...farmMembersUpdateSchema,
				response: { 200: farmMembersResponseSchema },
			},
		},
		updateFarmMember
	);

	fastify.delete(
		"/farm-members/:id",
		{
			schema: {
				...farmMembersIdParamSchema,
				response: { 200: { type: "object", properties: { message: { type: "string" } }, required: ["message"] } },
			},
		},
		deleteFarmMember
	);
}
