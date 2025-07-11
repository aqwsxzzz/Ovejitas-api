import { RouteGenericInterface } from "fastify";

export interface AnimalMeasurementAttributes {
  id: number;
  animalId: number;
  measurementType: 'weight' | 'height' | 'body_condition';
  value: number;
  unit: string;
  measuredAt: Date;
  measuredBy?: number | null;
  method?: string | null;
  notes?: string | null;
  createdAt: Date;
  updatedAt: Date;
}

export type AnimalMeasurementCreationAttributes = Omit<
  AnimalMeasurementAttributes, 
  'id' | 'createdAt' | 'updatedAt'
> & {
  measuredAt?: Date;
};

export interface IAnimalMeasurementCreateBody {
  measurementType: 'weight' | 'height' | 'body_condition';
  value: number;
  unit: string;
  measuredAt?: string;
  method?: string;
  notes?: string;
}

export interface IAnimalMeasurementUpdateBody {
  value?: number;
  unit?: string;
  measuredAt?: string;
  method?: string;
  notes?: string;
}

export interface IAnimalMeasurementParams {
  farmId: string;
  animalId: string;
  measurementId: string;
}

export interface AnimalMeasurementCreateRoute extends RouteGenericInterface {
  Body: IAnimalMeasurementCreateBody;
  Params: Pick<IAnimalMeasurementParams, 'farmId' | 'animalId'>;
}

export interface AnimalMeasurementUpdateRoute extends RouteGenericInterface {
  Body: IAnimalMeasurementUpdateBody;
  Params: IAnimalMeasurementParams;
}

export interface AnimalMeasurementGetRoute extends RouteGenericInterface {
  Params: IAnimalMeasurementParams;
}

export interface AnimalMeasurementListRoute extends RouteGenericInterface {
  Params: Pick<IAnimalMeasurementParams, 'farmId' | 'animalId'>;
  Querystring: {
    measurementType?: 'weight' | 'height' | 'body_condition';
    startDate?: string;
    endDate?: string;
    limit?: number;
  };
}