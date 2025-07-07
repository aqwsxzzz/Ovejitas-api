import { RouteGenericInterface } from "fastify";
import { UserLanguage } from "../models/user-model";
import { SpeciesTranslation } from "../models/species-translation-model";

export interface SpeciesCreateRoute extends RouteGenericInterface {
	Body: ISpeciesCreateBody;
}

interface ISpeciesCreateBody {
	languageCode: UserLanguage;
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
	translations?: SpeciesTranslation[];
}

export type SpeciesCreationAttributes = {};
