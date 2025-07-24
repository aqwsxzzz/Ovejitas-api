import { BaseService } from '../../services/base.service';
import { AnimalModel } from './animal.model';
import { AnimalCreate } from './animal.schema';
import { decodeId } from '../../utils/id-hash-util';
import { IncludeParser, TypedIncludeConfig } from '../../utils/include-parser';
import { FindOptions } from 'sequelize';

export class AnimalService extends BaseService {

	private static readonly ALLOWED_INCLUDES = IncludeParser.createConfig({
		species: {
			model: 'Species' as const,
			as: 'species',
			attributes: ['id', 'createdAt', 'updatedAt'],
			nested: {
				translations: {
					model: 'SpeciesTranslation' as const,
					as: 'translations',
					attributes: ['id', 'language', 'name', 'createdAt', 'updatedAt'],
				},
			},
		},
		breed: {
			model: 'Breed' as const,
			as: 'breed',
			attributes: ['id', 'name', 'createdAt', 'updatedAt', 'speciesId'],
		},
		father: {
			model: 'Animal' as const,
			as: 'father',
			attributes: ['id', 'name', 'createdAt', 'updatedAt', 'tagNumber'],
		},
		mother: {
			model: 'Animal' as const,
			as: 'mother',
			attributes: ['id', 'name', 'createdAt', 'updatedAt', 'tagNumber'],
		},
	} satisfies TypedIncludeConfig);

	async getAnimals(farmId: number, includeParam?: string): Promise<AnimalModel[] | null> {

		const findOptions: FindOptions = {
			where: {
				farmId,
			},
		};

		if (includeParam) {
			this.validateIncludes(includeParam, AnimalService.ALLOWED_INCLUDES);
			findOptions.include = this.parseIncludes(includeParam, AnimalService.ALLOWED_INCLUDES);
		}

		return this.db.models.Animal.findAll(findOptions);
	}

	async createAnimal({ data }:{ data: AnimalCreate & {farmId: number} }): Promise<AnimalModel | null> {

		const { breedId, speciesId, fatherId, motherId } = await this.decodeAnimalIds(data);
		return this.db.models.Animal.create({ ...data, breedId, speciesId, fatherId, motherId });
	}

	private async decodeAnimalIds(ids: {breedId: string, speciesId: string, fatherId?: string | undefined, motherId? : string  | undefined})  {
		return {
			breedId: decodeId(ids.breedId)!,
			speciesId: decodeId(ids.speciesId)!,
			fatherId: ids.fatherId ? decodeId(ids.fatherId) : undefined,
			motherId: ids.motherId ? decodeId(ids.motherId) : undefined,
		};
	}

}
