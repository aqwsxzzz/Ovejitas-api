import { FastifyReply, FastifyRequest } from "fastify";
import { FarmMembers } from "../../models/farm-members-model";
import { FarmMemberRole } from "../../types/farm-members-types";
import { serializeFarmMembers, serializeFarmMembersArray } from "../../serializers/farm-members-serializer";
import { decodeId } from "../../utils/id-hash-util";
import { User } from "../../models/user-model";

export const createFarmMember = async (request: FastifyRequest<{ Params: { farmId: string }; Body: { userId: string; role: FarmMemberRole } }>, reply: FastifyReply) => {
	const { farmId } = request.params;
	const { userId, role } = request.body;
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

export const getFarmMembersByFarmId = async (request: FastifyRequest<{ Params: { farmId: string } }>, reply: FastifyReply) => {
	const { farmId } = request.params;
	try {
		const farmMembers = await FarmMembers.findAll({
			where: { farmId: decodeId(farmId) },
			include: [{ model: User, as: "user" }],
		});
		reply.send(serializeFarmMembersArray(farmMembers));
	} catch (error) {
		reply.code(500).send({ message: "Failed to fetch farm members", error: error instanceof Error ? error.message : error });
	}
};

export const getFarmMemberById = async (request: FastifyRequest<{ Params: { farmId: string; memberId: string } }>, reply: FastifyReply) => {
	const { farmId, memberId } = request.params;
	const farmMember = await FarmMembers.findOne({
		where: { id: decodeId(memberId), farmId: decodeId(farmId) },
		include: [{ model: User, as: "user" }],
	});
	if (!farmMember) {
		return reply.code(404).send({ message: "Farm member not found" });
	}
	reply.send(serializeFarmMembers(farmMember));
};

export const updateFarmMember = async (request: FastifyRequest<{ Params: { farmId: string; memberId: string }; Body: { role: FarmMemberRole } }>, reply: FastifyReply) => {
	const { farmId, memberId } = request.params;
	const { role } = request.body;
	const farmMember = await FarmMembers.findOne({ where: { id: decodeId(memberId), farmId: decodeId(farmId) } });
	if (!farmMember) {
		return reply.code(404).send({ message: "Farm member not found" });
	}
	farmMember.setDataValue("role", role);
	await farmMember.save();
	reply.send(serializeFarmMembers(farmMember));
};

export const deleteFarmMember = async (request: FastifyRequest<{ Params: { farmId: string; memberId: string } }>, reply: FastifyReply) => {
	const { farmId, memberId } = request.params;
	const farmMember = await FarmMembers.findOne({ where: { id: decodeId(memberId), farmId: decodeId(farmId) } });
	if (!farmMember) {
		return reply.code(404).send({ message: "Farm member not found" });
	}
	await farmMember.destroy();
	reply.send({ message: "Farm member deleted" });
};
