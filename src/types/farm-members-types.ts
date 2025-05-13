import { RouteGenericInterface } from "fastify";

export type FarmMemberRole = "owner" | "member";

export interface FarmMembersAttributes {
	id: number;
	farmId: number;
	userId: number;
	role: FarmMemberRole;
	createdAt?: Date;
	updatedAt?: Date;
}

export type FarmMembersCreationAttributes = Pick<FarmMembersAttributes, "farmId" | "userId" | "role">;

export interface IFarmMembersIdParam {
	id: string;
}

export interface IFarmMembersCreateBody {
	farmId: string;
	userId: string;
	role: FarmMemberRole;
}

export interface IFarmMembersUpdateBody {
	role: FarmMemberRole;
}

export interface FarmMembersCreateRoute extends RouteGenericInterface {
	Body: IFarmMembersCreateBody;
}

export interface FarmMembersUpdateRoute extends RouteGenericInterface {
	Params: IFarmMembersIdParam;
	Body: IFarmMembersUpdateBody;
}

export interface FarmMembersDeleteRoute extends RouteGenericInterface {
	Params: IFarmMembersIdParam;
}
