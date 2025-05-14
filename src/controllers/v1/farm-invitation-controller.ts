import { FastifyReply, FastifyRequest } from "fastify";
import { FarmInvitation } from "../../models/farm-invitation-model";
import { FarmMembers } from "../../models/farm-members-model";
import { User, UserLanguage } from "../../models/user-model";
import { decodeId } from "../../utils/id-hash-util";
import { serializeFarmInvitation } from "../../serializers/farm-invitation-serializer";
import { isAlreadyMemberOrInvited, getUserFarmCount } from "../../utils/farm-invitation-util";
import { IFarmInvitationCreateBody, IFarmInvitationAcceptBody, IFarmInvitationIdParam, ISendInvitationParams } from "../../types/farm-invitation-types";
import { hashPassword } from "../../utils/password-util";
import { createInvitationToken } from "../../utils/token-util";

const MAX_FREE_USER_FARMS = 2;
const INVITATION_EXPIRY_DAYS = 7;

export const sendInvitation = async (request: FastifyRequest<{ Params: ISendInvitationParams; Body: IFarmInvitationCreateBody }>, reply: FastifyReply) => {
	const { farmId } = request.params;
	const { email } = request.body;

	const decodedFarmId = decodeId(farmId);
	if (typeof decodedFarmId !== "number") return reply.code(400).send({ message: "Invalid farm ID" });

	const check = await isAlreadyMemberOrInvited(email, decodedFarmId);

	if (check.alreadyMember) return reply.code(400).send({ message: "User is already a member of this farm" });
	if (check.alreadyInvited) return reply.code(400).send({ message: "User is already invited to this farm" });

	const user = await User.findOne({ where: { email } });

	if (user) {
		const farmCount = await getUserFarmCount(user.id);
		if (farmCount >= MAX_FREE_USER_FARMS) {
			return reply.code(400).send({ message: "User has reached the maximum number of farm memberships" });
		}
	}

	const token = createInvitationToken();
	const expiresAt = new Date(Date.now() + INVITATION_EXPIRY_DAYS * 24 * 60 * 60 * 1000);
	const invitation = await FarmInvitation.create({
		email,
		farmId: String(decodedFarmId),
		token,
		role: "member",
		status: "pending",
		expiresAt,
	});
	reply.code(201).send(serializeFarmInvitation(invitation, true));
};

export const acceptInvitation = async (request: FastifyRequest<{ Body: IFarmInvitationAcceptBody }>, reply: FastifyReply) => {
	const { token, password, displayName, language } = request.body;
	const invitation = await FarmInvitation.findOne({ where: { token, status: "pending" } });

	if (!invitation) return reply.code(400).send({ message: "Invalid or expired invitation token" });

	if (!decodeId(invitation.farmId)) return reply.code(400).send({ message: "Invalid farm ID" });

	if (!invitation.expiresAt || invitation.expiresAt.getTime() < Date.now()) {
		invitation.setDataValue("status", "expired");
		await invitation.save();
		return reply.code(400).send({ message: "Invitation has expired" });
	}

	let user = await User.findOne({ where: { email: invitation.email } });

	if (!user) {
		const hashedPassword = await hashPassword(password);
		user = await User.create({
			displayName,
			email: invitation.email,
			password: hashedPassword,
			language: (language as UserLanguage) || UserLanguage.ES,
		});
	}
	const farmCount = await getUserFarmCount(user.id);

	if (farmCount >= MAX_FREE_USER_FARMS) {
		return reply.code(400).send({ message: "You have reached the maximum number of farm memberships" });
	}

	await FarmMembers.create({
		farmId: decodeId(invitation.farmId)!,
		userId: user.id,
		role: "member",
	});

	invitation.setDataValue("status", "accepted");
	await invitation.save();

	reply.send({ message: "Invitation accepted" });
};

export const listInvitations = async (request: FastifyRequest<{ Params: ISendInvitationParams }>, reply: FastifyReply) => {
	const { farmId } = request.params;
	const decodedFarmId = decodeId(farmId);

	if (typeof decodedFarmId !== "number") return reply.code(400).send({ message: "Invalid farm ID" });

	const invitations = await FarmInvitation.findAll({
		where: { farmId: String(decodedFarmId), status: "pending" },
	});

	reply.send(invitations.map((inv) => serializeFarmInvitation(inv)));
};

export const cancelInvitation = async (request: FastifyRequest<{ Params: IFarmInvitationIdParam }>, reply: FastifyReply) => {
	const { invitationId } = request.params;
	const decodedInvitationId = decodeId(invitationId);
	if (typeof decodedInvitationId !== "number") return reply.code(400).send({ message: "Invalid invitation ID" });

	const invitation = await FarmInvitation.findByPk(decodedInvitationId);
	if (!invitation) return reply.code(404).send({ message: "Invitation not found" });

	invitation.setDataValue("status", "cancelled");
	await invitation.save();
	reply.send({ message: "Invitation cancelled" });
};
