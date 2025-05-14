import { UserRole } from "../models/user-model";
import { FarmMemberRole } from "./farm-members-types";

export type FarmInvitationStatus = "pending" | "accepted" | "expired" | "cancelled";

export interface FarmInvitationAttributes {
	id: string;
	email: string;
	farmId: string;
	role: FarmMemberRole;
	token: string;
	status: FarmInvitationStatus;
	createdAt?: string;
	updatedAt?: string;
	expiresAt?: Date;
}

export type FarmInvitationCreationAttributes = Pick<FarmInvitationAttributes, "email" | "farmId" | "role" | "token" | "status" | "expiresAt">;

export interface IFarmInvitationCreateBody {
	email: string;
	role: FarmMemberRole;
}

export interface IFarmInvitationAcceptBody {
	token: string;
	password: string;
	displayName: string;
	language?: string;
}

export interface IFarmInvitationIdParam {
	invitationId: string;
}

export interface ISendInvitationParams {
	farmId: string;
}
