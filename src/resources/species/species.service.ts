import { IncludeParser, TypedIncludeConfig } from '../../utils/include-parser';
import { SpeciesModel } from './species.model';
import { SpeciesTranslationModel } from '../species-translation/species-translation.model';
import { SpeciesCreateInput } from './species.schema';
import { FindOptions } from 'sequelize';
import { BaseService } from '../../services/base.service';
import { OrderParser, TypedOrderConfig } from '../../utils/order-parser';

export class SpeciesService extends BaseService {

	private static readonly ALLOWED_ORDERS = OrderParser.createConfig({
		id: {
			attribute: 'id',
		},

	} satisfies TypedOrderConfig);

	private static readonly ALLOWED_INCLUDES = IncludeParser.createConfig({
		translations: {
			model: 'SpeciesTranslation' as const,
			as: 'translations',
			attributes: ['id', 'language', 'name', 'createdAt', 'updatedAt'],
			nested: {
				language: {
					model: 'Language' as const,
					as: 'languageDetails',
				},
			},
		},

	} satisfies TypedIncludeConfig);

	async createSpecies(
		speciesData: SpeciesCreateInput,
	): Promise<{ species: SpeciesModel; translation: SpeciesTranslationModel }> {
		const species = await this.db.models.Species.create({});
		const translation = await this.db.models.SpeciesTranslation.create({
			language: speciesData.language,
			name: speciesData.name,
			speciesId: species.id,
		});
		return { species, translation };
	}

	/**
   * Get all species with optional includes
   * @param includeParam - Comma-separated string of relations to include
   * @returns Promise<SpeciesModel[]>
   * @throws Error if invalid includes are requested
   */
	async getAllSpecies(includeParam?: string, order?: string): Promise<SpeciesModel[]> {
		const findOptions: FindOptions = {};

		if (includeParam) {
			// Validate includes before parsing
			this.validateIncludes(includeParam, SpeciesService.ALLOWED_INCLUDES);
			findOptions.include = this.parseIncludes(includeParam, SpeciesService.ALLOWED_INCLUDES);
		}

		if (order) {
			// Validate orders before parsing
			this.validateOrder(order, SpeciesService.ALLOWED_ORDERS);
			findOptions.order = this.parseOrder(order, SpeciesService.ALLOWED_ORDERS);
		}

		return await this.db.models.Species.findAll(findOptions);
	}

	/**
   * Get species by ID with optional includes
   * @param id - Species ID
   * @param includeParam - Comma-separated string of relations to include
   * @returns Promise<SpeciesModel | null>
   * @throws Error if invalid includes are requested
   */
	async getSpeciesById(id: number, includeParam?: string): Promise<SpeciesModel | null> {
		const findOptions: FindOptions = { where: { id } };

		if (includeParam) {
			this.validateIncludes(includeParam, SpeciesService.ALLOWED_INCLUDES);
			findOptions.include = this.parseIncludes(includeParam, SpeciesService.ALLOWED_INCLUDES);
		}

		return await this.db.models.Species.findOne(findOptions);
	}

}
