import { BaseService } from '../../services/base.service';
import { FlockModel } from './flock.model';
import { FlockCreate, FlockStatus, FlockType, FlockUpdate } from './flock.schema';
import { decodeId } from '../../utils/id-hash-util';
import { IncludeParser, TypedIncludeConfig } from '../../utils/include-parser';
import { FindOptions, Op } from 'sequelize';
import { UserLanguage } from '../user/user.schema';
import { FilterConfig, FilterConfigBuilder } from '../../utils/filter-parser';
import { PaginatedResult, PaginationParams } from '../../utils/pagination';

export class FlockService extends BaseService {

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
			attributes: ['id', 'createdAt', 'updatedAt', 'speciesId'],
			nested: {
				translations: {
					model: 'BreedTranslation' as const,
					as: 'translations',
					attributes: ['id', 'breedId', 'language', 'name', 'createdAt', 'updatedAt'],
				},
			},
		},
	} satisfies TypedIncludeConfig);

	private static readonly ALLOWED_FILTERS: FilterConfig = {
		status: FilterConfigBuilder.enum('status', Object.values(FlockStatus)),
		flockType: FilterConfigBuilder.enum('flockType', Object.values(FlockType)),
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

	async getFlocks(farmId: number, language: UserLanguage, includeParam?: string, filters?: Record<string, string>, pagination?: PaginationParams): Promise<PaginatedResult<FlockModel>> {
		let includes = this.parseIncludes(includeParam, FlockService.ALLOWED_INCLUDES);
		const filterWhere = this.parseFilters(filters, FlockService.ALLOWED_FILTERS);

		if (includeParam?.includes('species.translations') || includeParam?.includes('breed.translations')) {
			includes = this.filterTranslationsByLanguage(includes, language);
		}

		const findOptions: FindOptions = {
			where: {
				farmId,
				...filterWhere,
			},
			include: includes,
		};

		return this.findAllPaginated(this.db.models.Flock, findOptions, pagination!);
	}

	async getFlockById(id: number, language: UserLanguage, includeParam?: string): Promise<FlockModel | null> {
		let includes = this.parseIncludes(includeParam, FlockService.ALLOWED_INCLUDES);

		if (includeParam?.includes('species.translations') || includeParam?.includes('breed.translations')) {
			includes = this.filterTranslationsByLanguage(includes, language);
		}

		return this.db.models.Flock.findByPk(id, { include: includes });
	}

	async createFlock({ data, language }: { data: FlockCreate & { farmId: number }, language: UserLanguage }): Promise<FlockModel | null> {
		return this.db.sequelize.transaction(async (transaction) => {
			const speciesId = decodeId(data.speciesId);
			const breedId = decodeId(data.breedId);

			if (!speciesId || !breedId) {
				throw new Error('Invalid species or breed ID');
			}

			await this.validateBreedSpeciesMatch(breedId, speciesId, transaction);
			await this.validateNameUniqueness(data.name, data.farmId, transaction);

			const { language: _language, speciesId: _speciesId, breedId: _breedId, ...rest } = data;

			const flock = await this.db.models.Flock.create({
				...rest,
				speciesId,
				breedId,
				currentCount: data.initialCount,
			}, { transaction });

			return this.db.models.Flock.findByPk(flock.id, {
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
					{
						model: this.db.models.Breed,
						as: 'breed',
						attributes: ['id', 'createdAt', 'updatedAt', 'speciesId'],
						include: [
							{
								model: this.db.models.BreedTranslation,
								as: 'translations',
								attributes: ['id', 'breedId', 'language', 'name', 'createdAt', 'updatedAt'],
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

	async updateFlock(id: number, farmId: number, data: FlockUpdate): Promise<FlockModel | null> {
		return this.db.sequelize.transaction(async (transaction) => {
			const flock = await this.db.models.Flock.findOne({
				where: { id, farmId },
				transaction,
				lock: true,
			});

			if (!flock) {
				throw new Error('Flock not found');
			}

			if (data.name && data.name !== flock.name) {
				await this.validateNameUniqueness(data.name, farmId, transaction, id);
			}

			await flock.update(data, { transaction });

			return flock;
		});
	}

	async deleteFlock(id: number, farmId: number): Promise<boolean> {
		return this.db.sequelize.transaction(async (transaction) => {
			const flock = await this.db.models.Flock.findOne({
				where: { id, farmId },
				transaction,
			});

			if (!flock) {
				return false;
			}

			await flock.destroy({ transaction });
			return true;
		});
	}

	private async validateBreedSpeciesMatch(breedId: number, speciesId: number, transaction: import('sequelize').Transaction): Promise<void> {
		const breed = await this.db.models.Breed.findByPk(breedId, { transaction });
		if (!breed) {
			throw new Error('Breed not found.');
		}
		if (breed.speciesId !== speciesId) {
			throw new Error('Selected breed does not belong to the specified species.');
		}
	}

	private async validateNameUniqueness(name: string, farmId: number, transaction: import('sequelize').Transaction, excludeId?: number): Promise<void> {
		const where: Record<string, unknown> = { name, farmId };
		if (excludeId) {
			where.id = { [Op.ne]: excludeId };
		}
		const existing = await this.db.models.Flock.findOne({
			where,
			transaction,
		});
		if (existing) {
			throw new Error('A flock with this name already exists on this farm.');
		}
	}
}
