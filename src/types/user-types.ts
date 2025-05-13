import { RouteGenericInterface } from "fastify";
import { UserLanguage, UserRole } from "../models/user-model";

interface IUserUpdateBody {
	displayName: string;
	email: string;
	isActive: boolean;
	role: UserRole;
	language: UserLanguage;
}

interface IUserUpdateParams {
	id: string;
}

interface IUserDeleteParams {
	id: string;
}

export interface UserDeleteRoute extends RouteGenericInterface {
	Params: IUserDeleteParams;
}

export interface UserUpdateRoute extends RouteGenericInterface {
	Params: IUserUpdateParams;
	Body: IUserUpdateBody;
}

export interface UserAttributes {
	id: number;
	displayName: string;
	email: string;
	password: string;
	isActive: boolean;
	role: UserRole;
	language: UserLanguage;
	lastVisitedFarmId?: number;
	createdAt?: Date;
	updatedAt?: Date;
}

export type UserCreationAttributes = Pick<UserAttributes, "displayName" | "email" | "password" | "language" | "lastVisitedFarmId">;
