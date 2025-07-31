import { IncludeParser, TypedIncludeConfig } from '../../utils/include-parser';
import { SpeciesModel } from './species.model';
import { SpeciesTranslationModel } from '../species-translation/species-translation.model';
import { SpeciesCreateInput } from './species.schema';
import { FindOptions } from 'sequelize';
import { BaseService } from '../../services/base.service';
import { OrderParser, TypedOrderConfig } from '../../utils/order-parser';
import { UserLanguage } from '../user/user.schema';

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

	async getAllSpecies(includeParam?: string, order?: string, language?: UserLanguage): Promise<SpeciesModel[]> {
		const findOptions: FindOptions = {};

		let includes = this.parseIncludes(includeParam, SpeciesService.ALLOWED_INCLUDES);

		// Filter translations by language if translations are included and language is provided
		if (includeParam?.includes('translations') && language) {
			includes = this.filterTranslationsByLanguage(includes, language);

			findOptions.include = includes;
		}

		findOptions.order = this.parseOrder(order, SpeciesService.ALLOWED_ORDERS);

		return await this.db.models.Species.findAll(findOptions);
	}

	async getSpeciesById(id: number,language: UserLanguage, includeParam?: string ): Promise<SpeciesModel | null> {
		const findOptions: FindOptions = { where: { id  } };

		let includes = this.parseIncludes(includeParam, SpeciesService.ALLOWED_INCLUDES);

		// Filter translations by language if translations are included
		if (includeParam?.includes('translations')) {
			includes = this.filterTranslationsByLanguage(includes, language);
		}

		findOptions.include = includes;

		return await this.db.models.Species.findOne(findOptions);
	}

}
