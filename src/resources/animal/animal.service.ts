import { BaseService } from '../../services/base.service';
import { AnimalModel } from './animal.model';
import { AnimalCreate, AnimalSex, AnimalUpdate } from './animal.schema';
import { decodeId } from '../../utils/id-hash-util';
import { IncludeParser, TypedIncludeConfig } from '../../utils/include-parser';
import { FindOptions, Transaction } from 'sequelize';
import { UserLanguage } from '../user/user.schema';
import { FilterConfig, FilterConfigBuilder } from '../../utils/filter-parser';

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

	private static readonly ALLOWED_FILTERS: FilterConfig = {
		sex: FilterConfigBuilder.enum('sex', Object.values(AnimalSex)),
		groupName: FilterConfigBuilder.string('groupName'),
	};

	async getAnimals(farmId: number,  language: UserLanguage, includeParam?: string, filters?: Record<string, string>): Promise<AnimalModel[] | null> {

		let includes = this.parseIncludes(includeParam, AnimalService.ALLOWED_INCLUDES);
		const filterWhere = this.parseFilters(filters, AnimalService.ALLOWED_FILTERS);

		// Filter species translations by language if species and translations are included
		if (includeParam?.includes('species.translations') ) {
			includes = this.filterTranslationsByLanguage(includes, language);
		}

		const findOptions: FindOptions = {
			where: {
				farmId,
				...filterWhere,
			},
			include: includes,
		};

		return this.db.models.Animal.findAll(findOptions);
	}

	async createAnimal({ data }: { data: AnimalCreate & { farmId: number } }): Promise<AnimalModel | null> {
		return this.db.sequelize.transaction(async (transaction) => {
			const { breedId, speciesId, fatherId, motherId } = await this.decodeAnimalIds(data);

			const { acquisitionDate, birthDate, ...rest } = data;

			if (fatherId || motherId) {
				await this.validateParents(fatherId, motherId, transaction);
			}

			await this.validateBreedSpeciesMatch(breedId, speciesId, transaction);
			await this.validateTagNumberUniqueness(data.tagNumber, data.farmId, speciesId, transaction);

			const createData = { ...rest, breedId, speciesId, fatherId, motherId, name: data.name || '', ...(birthDate ? { birthDate } : {}), ...(acquisitionDate ? { acquisitionDate } : {}) };

			return this.db.models.Animal.create(createData, { transaction });
		});
	}

	async getAnimalById(id: number,language: UserLanguage, includeParam?: string ): Promise<AnimalModel | null> {
		const findOptions: FindOptions = {};

		let includes = this.parseIncludes(includeParam, AnimalService.ALLOWED_INCLUDES);

		// Filter species translations by language if species and translations are included
		if (includeParam?.includes('species.translations')  ) {
			includes = this.filterTranslationsByLanguage(includes, language);
		}

		findOptions.include = includes;

		return await this.db.models.Animal.findByPk(id, findOptions);
	}

	async updateAnimal(id: number, farmId: number, data: AnimalUpdate): Promise<AnimalModel | null> {
		return this.db.sequelize.transaction(async (transaction) => {

			const animal = await this.db.models.Animal.findByPk(id, {
				transaction,
				lock: true, // Prevents other transactions from modifying this record
			});

			if (!animal) {
				throw new Error('Animal not found');
			}

			const { breedId, speciesId, fatherId, motherId } = await this.decodeAnimalIds(data);

			const { acquisitionDate, birthDate, ...rest } = data;

			if (fatherId || motherId) {
				await this.validateParents(fatherId, motherId, transaction);
			}

			await this.validateBreedSpeciesMatch(breedId, speciesId, transaction);
			await this.validateTagNumberUniqueness(data.tagNumber, farmId, speciesId, transaction);

			const createData = { ...rest, breedId, speciesId, fatherId, motherId, name: data.name || '', ...(birthDate ? { birthDate } : {}), ...(acquisitionDate ? { acquisitionDate } : {}) };

			await animal.update(createData, { transaction });

			return animal;
		});
	}

	private async decodeAnimalIds(ids: {breedId: string, speciesId: string, fatherId?: string | undefined, motherId? : string  | undefined})  {
		return {
			breedId: decodeId(ids.breedId)!,
			speciesId: decodeId(ids.speciesId)!,
			fatherId: ids.fatherId ? decodeId(ids.fatherId) : undefined,
			motherId: ids.motherId ? decodeId(ids.motherId) : undefined,
		};
	}

	private async validateParents(fatherId?: number, motherId?: number, transaction?: Transaction): Promise<void> {
		let father, mother;
		if (fatherId) father = await this.db.models.Animal.findByPk(fatherId, { transaction }) as AnimalModel;
		if (motherId) mother = await this.db.models.Animal.findByPk(motherId, { transaction }) as AnimalModel;

		const error = this.validateParentSex(father, mother);
		if (error) {
			throw new Error('Parents must be of opposite sex.');
		}
	}

	private validateParentSex(father?: AnimalModel , mother?: AnimalModel ): string | null {
		if (father && father.sex !== 'male') return 'Father must be male';
		if (mother && mother.sex !== 'female') return 'Mother must be female';
		return null;
	}

	private async validateBreedSpeciesMatch(breedId: number, speciesId: number, transaction?: Transaction): Promise<void> {
		const breed = await this.db.models.Breed.findByPk(breedId, { transaction });
		if (!breed) {
			throw new Error('Breed not found.');
		}
		if (breed.speciesId !== speciesId) {
			throw new Error('Selected breed does not belong to the specified species.');
		}
	}

	private async validateTagNumberUniqueness(tagNumber: string, farmId: number, speciesId: number, transaction:Transaction): Promise<void> {
		const existing = await this.db.models.Animal.findOne({
			where: { tagNumber, farmId, speciesId },
			transaction,
		});
		if (existing) {
			throw new Error('Tag number must be unique per farm and species.');
		}
	}

}
