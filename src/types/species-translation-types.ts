import { RouteGenericInterface } from 'fastify';
import { UserLanguage } from '../models/user-model';

interface ISpecieTranslationBody {
	speciesId: string;
	languageCode: UserLanguage;
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
	languageCode: UserLanguage;
	name: string;
	createdAt?: Date;
	updatedAt?: Date;
}

export type SpeciesTranslationCreationAttributes = Omit<SpeciesTranslationAttributes, 'id' | 'createdAt' | 'updatedAt'>;
