import { RouteGenericInterface } from "fastify";
export interface SpeciesCreateRoute extends RouteGenericInterface {
	Body: ISpeciesCreateBody;
}

interface ISpeciesCreateBody {
	languageCode: string;
	name: string;
}

export interface ISpeciesIdParam {
	id: string;
}

export interface IGetSpeciesByIdQuery {
	language: string;
}

export interface SpeciesListParams {
	language: string;
}

export interface SpeciesAttributes {
	id: number;
	createdAt?: Date;
	updatedAt?: Date;
}

export type SpeciesCreationAttributes = {};
