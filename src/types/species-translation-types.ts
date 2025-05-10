import { RouteGenericInterface } from "fastify";
interface ISpecieTranslationBody {
	speciesId: string;
	languageCode: string;
	name: string;
}

export interface ICreateSpecieBody extends RouteGenericInterface {
	Body: ISpecieTranslationBody;
}

export interface SpeciesTranslationIdParams {
	translationId: string;
}

export interface SpeciesTranslationAttributes {
	id: number;
	speciesId: number;
	languageCode: string;
	name: string;
	createdAt?: Date;
	updatedAt?: Date;
}

export type SpeciesTranslationCreationAttributes = Omit<SpeciesTranslationAttributes, "id" | "createdAt" | "updatedAt">;
