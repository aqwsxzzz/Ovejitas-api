import { UserLanguage, UserRole } from "../models/user-model";

export interface IUserUpdateBody {
	displayName: string;
	email: string;
	isActive: boolean;
	role: UserRole;
	language: UserLanguage;
}

export interface IUserUpdateParams {
	id: string;
}

export interface IUserDeleteParams {
	id: string;
}
