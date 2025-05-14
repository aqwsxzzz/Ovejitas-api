import { User, UserLanguage } from "../models/user-model";
import { Farm } from "../models/farm-model";
import { FarmMembers } from "../models/farm-members-model";
import { FarmInvitation } from "../models/farm-invitation-model";
import { FarmMemberRoleEnum } from "../types/farm-members-types";
import { decodeId } from "./id-hash-util";
import { hashPassword } from "./password-util";
import { AuthSignUpBody } from "../types/auth-types";
import { Transaction } from "sequelize";

export async function handleInvitationSignUp(body: AuthSignUpBody, transaction: Transaction) {
	const { displayName, email, password, language = "es", invitationToken } = body;
	const invitation = await FarmInvitation.findOne({ where: { token: invitationToken, status: "pending" }, transaction });
	if (!invitation) {
		throw new Error("Invalid or expired invitation token");
	}
	if (!invitation.expiresAt || invitation.expiresAt.getTime() < Date.now()) {
		invitation.setDataValue("status", "expired");
		await invitation.save({ transaction });
		throw new Error("Invitation has expired");
	}
	const hashedPassword = await hashPassword(password);
	const user = await User.create({ displayName, email, password: hashedPassword, language: language as UserLanguage }, { transaction });
	await FarmMembers.create({ farmId: decodeId(invitation.farmId)!, userId: user.id, role: invitation.role }, { transaction });
	user.set("lastVisitedFarmId", decodeId(invitation.farmId));
	await user.save({ transaction });
	invitation.setDataValue("status", "accepted");
	await invitation.save({ transaction });
	return user;
}

export async function handleDefaultSignUp(body: AuthSignUpBody, transaction: Transaction) {
	const { displayName, email, password, language = "es" } = body;
	const hashedPassword = await hashPassword(password);
	const user = await User.create({ displayName, email, password: hashedPassword, language: language as UserLanguage }, { transaction });
	const farmName = language === "en" ? "My farm" : "Mi Granja";
	const farm = await Farm.create({ name: farmName }, { transaction });
	await FarmMembers.create({ farmId: farm.id, userId: user.id, role: FarmMemberRoleEnum.OWNER }, { transaction });
	user.set("lastVisitedFarmId", farm.id);
	await user.save({ transaction });
	return user;
}
