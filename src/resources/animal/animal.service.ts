import { BaseService } from '../../services/base.service';
import { AnimalModel } from './animal.model';
import { AnimalBulkCreate, AnimalCreate, AnimalReproductiveStatus, AnimalSex, AnimalStatus, AnimalUpdate } from './animal.schema';
import { decodeId, encodeId } from '../../utils/id-hash-util';
import { IncludeParser, TypedIncludeConfig } from '../../utils/include-parser';
import { FindOptions, Transaction, QueryTypes } from 'sequelize';
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
		speciesId: {
			attribute: 'speciesId',
			operator: 'eq',
			type: 'number',
			transform: (value: string) => {
				const decoded = decodeId(value);
				if (!decoded) {
					throw new Error(`Invalid speciesId: ${value}`);
				}
				return decoded;
			},
		},
	};

	async getAnimals(farmId: number, language: UserLanguage, includeParam?: string, filters?: Record<string, string>): Promise<AnimalModel[] | null> {

		let includes = this.parseIncludes(includeParam, AnimalService.ALLOWED_INCLUDES);
		const filterWhere = this.parseFilters(filters, AnimalService.ALLOWED_FILTERS);

		// Filter species translations by language if species and translations are included
		if (includeParam?.includes('species.translations')) {
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

	async createAnimal({ data, language }: { data: AnimalCreate & { farmId: number }, language: UserLanguage }): Promise<AnimalModel | null> {
		return this.db.sequelize.transaction(async (transaction) => {
			const { breedId, speciesId, fatherId, motherId } = await this.decodeAnimalIds(data);

			const { acquisitionDate, birthDate, ...rest } = data;
			// Remove language from rest data
			delete (rest as Partial<AnimalCreate>).language;

			if (fatherId || motherId) {
				await this.validateParents(fatherId, motherId, transaction);
			}

			await this.validateBreedSpeciesMatch(breedId, speciesId, transaction);
			await this.validateTagNumberUniqueness(data.tagNumber, data.farmId, speciesId, transaction);

			const createData = { ...rest, breedId, speciesId, fatherId, motherId, name: data.name || '', ...(birthDate ? { birthDate } : {}), ...(acquisitionDate ? { acquisitionDate } : {}) };

			const animal = await this.db.models.Animal.create(createData, { transaction });

			// Fetch animal with species and translations
			return this.db.models.Animal.findByPk(animal.id, {
				include: [
					{
						model: this.db.models.Species,
						as: 'species',
						attributes: ['id', 'createdAt', 'updatedAt'],
						include: [
							{
								model: this.db.models.SpeciesTranslation,
								as: 'translations',
								attributes: ['id', 'language', 'name', 'createdAt', 'updatedAt'],
								where: { language },
								required: false,
							},
						],
					},
				],
				transaction,
			});
		});
	}

	async getAnimalById(id: number, language: UserLanguage, includeParam?: string): Promise<AnimalModel | null> {
		const findOptions: FindOptions = {};

		let includes = this.parseIncludes(includeParam, AnimalService.ALLOWED_INCLUDES);

		// Filter species translations by language if species and translations are included
		if (includeParam?.includes('species.translations')) {
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

	async bulkCreateAnimals({ data }: { data: AnimalBulkCreate & { farmId: number } }): Promise<{ created: AnimalModel[], failed: { tagNumber: string; reason: string }[] }> {
		const { farmId, groupName, speciesId: encodedSpeciesId, breedId: encodedBreedId } = data;

		// Decode and validate IDs
		const { speciesId, breedId } = this.decodeBulkCreateIds(encodedSpeciesId, encodedBreedId);

		// Generate or validate tag numbers
		const tagNumbers = this.generateTagNumbers(data);

		// Perform bulk creation with validation
		return await this.performBulkCreate({
			farmId,
			speciesId,
			breedId,
			tagNumbers,
			groupName: groupName || null,
		});
	}

	async getAnimalDashboard({ farmId, language }: { farmId: number, language: UserLanguage }): Promise<{ count: number, species: { id: string, name: string } }[]> {
		interface DashboardResult {
			count: string;
			speciesId: number;
			speciesName: string;
		}

		const results = await this.db.sequelize.query<DashboardResult>(
			`SELECT 
				a.species_id as "speciesId",
				COUNT(a.id) as count,
				st.name as "speciesName"
			FROM animals a
			LEFT JOIN species s ON a.species_id = s.id
			LEFT JOIN species_translation st ON s.id = st.species_id AND st.language_code = :language
			WHERE a.farm_id = :farmId
			GROUP BY a.species_id, st.name
			ORDER BY count DESC`,
			{
				replacements: { farmId, language },
				type: QueryTypes.SELECT,
			},
		);

		return results.map((result) => ({
			count: parseInt(result.count),
			species: {
				id: encodeId(result.speciesId),
				name: result.speciesName || '',
			},
		}));
	}

	async deleteAnimal(id: number, farmId: number): Promise<boolean> {
		return this.db.sequelize.transaction(async (transaction) => {
			const animal = await this.db.models.Animal.findOne({
				where: { id, farmId },
				transaction,
			});

			if (!animal) {
				return false;
			}

			await animal.destroy({ transaction });
			return true;
		});
	}

	private decodeBulkCreateIds(encodedSpeciesId: string, encodedBreedId: string): { speciesId: number; breedId: number } {
		const speciesId = decodeId(encodedSpeciesId);
		const breedId = decodeId(encodedBreedId);

		if (!speciesId || !breedId) {
			throw new Error('Invalid species or breed ID');
		}

		return { speciesId, breedId };
	}

	private generateTagNumbers(data: AnimalBulkCreate): string[] {
		const { tags, tagPrefix, tagStartNumber, count } = data;

		// Use provided tags if available
		if (tags && tags.length > 0) {
			return tags;
		}

		// Generate tags from start number and count
		if (tagStartNumber && count) {
			const generatedTags: string[] = [];
			for (let i = 0; i < count; i++) {
				const tagNumber = tagPrefix
					? `${tagPrefix}${tagStartNumber + i}`
					: `${tagStartNumber + i}`;
				generatedTags.push(tagNumber);
			}
			return generatedTags;
		}

		throw new Error('Either provide tags array or tagStartNumber with count');
	}

	private async performBulkCreate(params: {
		farmId: number;
		speciesId: number;
		breedId: number;
		tagNumbers: string[];
		groupName: string | null;
	}): Promise<{ created: AnimalModel[]; failed: { tagNumber: string; reason: string }[] }> {
		const { farmId, speciesId, breedId, tagNumbers, groupName } = params;
		const failedTags: { tagNumber: string; reason: string }[] = [];

		const createdAnimals = await this.db.sequelize.transaction(async (transaction) => {
			// Validate breed/species match
			await this.validateBreedSpeciesMatch(breedId, speciesId, transaction);

			// Check for existing tags
			const validTags = await this.filterExistingTags({
				tagNumbers,
				farmId,
				speciesId,
				transaction,
				failedTags,
			});

			// Create animals for valid tags
			if (validTags.length > 0) {
				const animalData = this.prepareBulkAnimalData({
					validTags,
					farmId,
					speciesId,
					breedId,
					groupName,
				});
				return await this.db.models.Animal.bulkCreate(animalData, { transaction });
			}

			return [];
		});

		return {
			created: createdAnimals,
			failed: failedTags,
		};
	}

	private async filterExistingTags(params: {
		tagNumbers: string[];
		farmId: number;
		speciesId: number;
		transaction: Transaction;
		failedTags: { tagNumber: string; reason: string }[];
	}): Promise<string[]> {
		const { tagNumbers, farmId, speciesId, transaction, failedTags } = params;

		// Find all existing tags in one query
		const existingAnimals = await this.db.models.Animal.findAll({
			where: {
				tagNumber: tagNumbers,
				farmId,
				speciesId,
			},
			attributes: ['tagNumber'],
			transaction,
		});

		const existingTagNumbers = new Set(existingAnimals.map(a => a.tagNumber));
		const validTags: string[] = [];

		// Separate valid and invalid tags
		for (const tagNumber of tagNumbers) {
			if (existingTagNumbers.has(tagNumber)) {
				failedTags.push({
					tagNumber,
					reason: 'Tag number already exists for this farm and species',
				});
			} else {
				validTags.push(tagNumber);
			}
		}

		return validTags;
	}

	private prepareBulkAnimalData(params: {
		validTags: string[];
		farmId: number;
		speciesId: number;
		breedId: number;
		groupName: string | null;
	}) {
		const { validTags, farmId, speciesId, breedId, groupName } = params;

		return validTags.map(tagNumber => ({
			farmId,
			speciesId,
			breedId,
			tagNumber,
			groupName,
			name: '',
			sex: AnimalSex.Unknown,
			status: AnimalStatus.Alive,
			reproductiveStatus: AnimalReproductiveStatus.Other,
		}));
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
