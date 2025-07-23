import { Database } from '../../database';
import { SpeciesTranslationModel } from './species-translation.model';
import { CreateSpeciesTranslation } from './species-translation.schema';

export class SpeciesTranslationService {
	private db: Database;

	constructor(db: Database) {
		this.db = db;
	}

	async createSpeciesTranslation(speciesTranslationData: CreateSpeciesTranslation): Promise<SpeciesTranslationModel> {
		const speciesTranslation = await this.db.models.SpeciesTranslation.create(speciesTranslationData);
		return speciesTranslation;
	}

}
