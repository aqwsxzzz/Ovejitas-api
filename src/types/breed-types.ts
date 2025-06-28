import { RouteGenericInterface } from "fastify";

export interface BreedAttributes {
	id: number;
	speciesId: number;
	name: string;
	createdAt?: Date;
	updatedAt?: Date;
}

export type BreedCreationAttributes = Omit<BreedAttributes, "id" | "createdAt" | "updatedAt">;

export interface IBreedCreateBody {
	speciesId: string; // encoded
	name: string;
}

export interface IBreedUpdateBody {
	name?: string;
	speciesId?: string; // encoded
}

export interface IBreedIdParam {
	id: string; // encoded
}

export interface BreedCreateRoute extends RouteGenericInterface {
	Body: IBreedCreateBody;
}

export interface BreedUpdateRoute extends RouteGenericInterface {
	Params: IBreedIdParam;
	Body: IBreedUpdateBody;
}

export interface BreedDeleteRoute extends RouteGenericInterface {
	Params: IBreedIdParam;
}

export interface BreedGetRoute extends RouteGenericInterface {
	Params: IBreedIdParam;
}

export interface BreedListQuery {
	speciesId?: string; // encoded, optional
}

export interface BreedListRoute extends RouteGenericInterface {
	Querystring: BreedListQuery;
}
