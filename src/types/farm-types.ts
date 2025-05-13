import { RouteGenericInterface } from "fastify";

export interface FarmAttributes {
	id: number;
	name: string;
	createdAt?: Date;
	updatedAt?: Date;
}

export interface FarmCreationAttributes extends Pick<FarmAttributes, "name"> {}

export interface IFarmIdParam {
	id: string;
}

export interface IFarmUpdateBody {
	name: string;
}

export interface FarmCreateRoute extends RouteGenericInterface {
	Body: FarmCreationAttributes;
}

export interface FarmUpdateRoute extends RouteGenericInterface {
	Params: IFarmIdParam;
	Body: IFarmUpdateBody;
}

export interface FarmDeleteRoute extends RouteGenericInterface {
	Params: IFarmIdParam;
}
