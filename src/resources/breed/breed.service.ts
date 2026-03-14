import { BaseService } from '../../services/base.service';
import { BreedModel } from './breed.model';
import { BreedTranslationModel } from '../breed-translation/breed-translation.model';
import { IncludeParser, TypedIncludeConfig } from '../../utils/include-parser';
import { OrderParser, TypedOrderConfig } from '../../utils/order-parser';
import { FindOptions } from 'sequelize';
import { UserLanguage } from '../user/user.schema';
import { PaginatedResult, PaginationParams } from '../../utils/pagination';

export class BreedService extends BaseService {

	private static readonly ALLOWED_ORDERS = OrderParser.createConfig({
		id: {
			attribute: 'id',
		},
		createdAt: {
			attribute: 'createdAt',
		},
	} satisfies TypedOrderConfig);

	private static readonly ALLOWED_INCLUDES = IncludeParser.createConfig({
		translations: {
			model: 'BreedTranslation' as const,
			as: 'translations',
			attributes: ['id', 'breedId', 'language', 'name', 'createdAt', 'updatedAt'],
		},
	} satisfies TypedIncludeConfig);

	async createBreed({ name, language, speciesId }: { name: string; language: string; speciesId: number }): Promise<{ breed: BreedModel; translation: BreedTranslationModel }> {
		const breed = await this.db.models.Breed.create({ speciesId });
		const translation = await this.db.models.BreedTranslation.create({
			breedId: breed.id,
			language,
			name,
		});
		return { breed, translation };
	}

	async getBreedsBySpecies(speciesId: number, order?: string, includeParam?: string, language?: UserLanguage, pagination?: PaginationParams): Promise<PaginatedResult<BreedModel>> {
		const findOptions: FindOptions = {
			where: { speciesId },
		};

		let includes = this.parseIncludes(includeParam, BreedService.ALLOWED_INCLUDES);

		if (includeParam?.includes('translations') && language) {
			includes = this.filterTranslationsByLanguage(includes, language);
		}

		findOptions.include = includes;
		findOptions.order = this.parseOrder(order, BreedService.ALLOWED_ORDERS);

		return this.findAllPaginated(this.db.models.Breed, findOptions, pagination!);
	}
}
