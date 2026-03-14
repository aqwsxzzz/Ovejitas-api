import { BaseService } from '../../services/base.service';
import { BreedTranslationModel } from './breed-translation.model';

interface CreateBreedTranslationInput {
	breedId: number;
	language: string;
	name: string;
}

export class BreedTranslationService extends BaseService {

	async createBreedTranslation(data: CreateBreedTranslationInput): Promise<BreedTranslationModel> {
		const breedTranslation = await this.db.models.BreedTranslation.create(data);
		return breedTranslation;
	}

}
