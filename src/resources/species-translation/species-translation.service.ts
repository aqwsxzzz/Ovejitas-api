
import { BaseService } from '../../services/base.service';
import { SpeciesTranslationModel } from './species-translation.model';
import { CreateSpeciesTranslation } from './species-translation.schema';

export class SpeciesTranslationService extends BaseService {

	async createSpeciesTranslation(speciesTranslationData: CreateSpeciesTranslation): Promise<SpeciesTranslationModel> {
		const speciesTranslation = await this.db.models.SpeciesTranslation.create(speciesTranslationData);
		return speciesTranslation;
	}

}
