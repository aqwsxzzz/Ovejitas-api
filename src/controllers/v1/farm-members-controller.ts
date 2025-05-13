import { FastifyReply, FastifyRequest } from "fastify";
import { FarmMembers } from "../../models/farm-members-model";
import { FarmMembersCreateRoute, FarmMembersUpdateRoute, FarmMembersDeleteRoute, IFarmMembersIdParam, FarmMemberRole } from "../../types/farm-members-types";
import { serializeFarmMembers } from "../../serializers/farm-members-serializer";
import { decodeId } from "../../utils/id-hash-util";

export const createFarmMember = async (request: FastifyRequest<FarmMembersCreateRoute>, reply: FastifyReply) => {
	const { farmId, userId, role }: { farmId: string; userId: string; role: FarmMemberRole } = request.body;
	try {
		const farmMember = await FarmMembers.create({
			farmId: decodeId(farmId)!,
			userId: decodeId(userId)!,
			role,
		});
		reply.code(201).send(serializeFarmMembers(farmMember));
	} catch (error) {
		reply.code(500).send({ message: "Failed to create farm member", error: error instanceof Error ? error.message : error });
	}
};

export const getFarmMemberById = async (request: FastifyRequest<{ Params: IFarmMembersIdParam }>, reply: FastifyReply) => {
	const { id } = request.params;
	const farmMember = await FarmMembers.findByPk(decodeId(id));
	if (!farmMember) {
		return reply.code(404).send({ message: "Farm member not found" });
	}
	reply.send(serializeFarmMembers(farmMember));
};

export const updateFarmMember = async (request: FastifyRequest<FarmMembersUpdateRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const { role }: { role: FarmMemberRole } = request.body;
	const farmMember = await FarmMembers.findByPk(decodeId(id));
	if (!farmMember) {
		return reply.code(404).send({ message: "Farm member not found" });
	}
	farmMember.setDataValue("role", role);
	await farmMember.save();
	reply.send(serializeFarmMembers(farmMember));
};

export const deleteFarmMember = async (request: FastifyRequest<FarmMembersDeleteRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const farmMember = await FarmMembers.findByPk(decodeId(id));
	if (!farmMember) {
		return reply.code(404).send({ message: "Farm member not found" });
	}
	await farmMember.destroy();
	reply.send({ message: "Farm member deleted" });
};
