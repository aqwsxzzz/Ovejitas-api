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

export interface IFarmMembersFarmIdParam {
	farmId: string;
}

export interface IFarmMembersFarmIdAndMemberIdParam {
	farmId: string;
	memberId: string;
}

export interface FarmMembersGetByFarmIdRoute extends RouteGenericInterface {
	Params: IFarmMembersFarmIdParam;
}

export interface FarmMembersCreateRoute extends RouteGenericInterface {
	Params: IFarmMembersFarmIdParam;
	Body: IFarmMembersCreateBody;
}

export interface FarmMembersGetByIdRoute extends RouteGenericInterface {
	Params: IFarmMembersFarmIdAndMemberIdParam;
}

export interface FarmMembersUpdateRoute extends RouteGenericInterface {
	Params: IFarmMembersFarmIdAndMemberIdParam;
	Body: IFarmMembersUpdateBody;
}

export interface FarmMembersDeleteRoute extends RouteGenericInterface {
	Params: IFarmMembersFarmIdAndMemberIdParam;
}
