import { RouteGenericInterface } from "fastify";

export interface AnimalAttributes {
	id: number;
	farmId: number;
	speciesId: number;
	breedId?: number | null;
	name: string;
	tagNumber?: string | null;
	sex: "male" | "female" | "unknown";
	birthDate: Date;
	weight?: number | null;
	status: "alive" | "sold" | "deceased" | string;
	reproductiveStatus: "open" | "pregnant" | "lactating" | "other" | string;
	fatherId?: number | null;
	motherId?: number | null;
	acquisitionType: "born" | "purchased" | "other" | string;
	acquisitionDate: Date;
	createdAt?: Date;
	updatedAt?: Date;
}

export type AnimalCreationAttributes = Omit<AnimalAttributes, "id" | "createdAt" | "updatedAt">;

export interface IAnimalCreateBody {
	speciesId: string;
	breedId?: string | null;
	name: string;
	tagNumber?: string | null;
	sex: "male" | "female" | "unknown";
	birthDate: string;
	weight?: number | null;
	status: "alive" | "sold" | "deceased" | string;
	reproductiveStatus: "open" | "pregnant" | "lactating" | "other" | string;
	fatherId?: string | null;
	motherId?: string | null;
	acquisitionType: "born" | "purchased" | "other" | string;
	acquisitionDate: string;
}

export interface IAnimalUpdateBody extends Partial<IAnimalCreateBody> {}

export interface IAnimalIdParam {
	id: string;
}

export interface AnimalCreateRoute extends RouteGenericInterface {
	Body: IAnimalCreateBody;
	Params: {
		farmId: string;
	};
}

export interface AnimalUpdateRoute extends RouteGenericInterface {
	Params: {
		farmId: string;
		id: string;
	};
	Body: IAnimalUpdateBody;
}

export interface AnimalDeleteRoute extends RouteGenericInterface {
	Params: IAnimalIdParam;
}

export interface AnimalGetRoute extends RouteGenericInterface {
	Params: IAnimalIdParam;
}

export interface AnimalListRoute extends RouteGenericInterface {
	Query: {
		farmId: string;
	};
}

export interface AnimalListByFarmParam {
	farmId: string;
}

export interface AnimalListByFarmRoute extends RouteGenericInterface {
	Params: AnimalListByFarmParam;
}
