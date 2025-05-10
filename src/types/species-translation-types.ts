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
