import { Database } from '../../database';
import { SpeciesTranslationModel } from '../species-translation/species-translation.model';
import { SpeciesModel } from './species.model';
import { SpeciesCreateInput } from './species.schema';

export class SpeciesService {
	private db: Database;
	constructor(db: Database) {
		this.db = db;
	}

	async createSpecies(speciesData: SpeciesCreateInput): Promise<{species: SpeciesModel, translation: SpeciesTranslationModel}> {
		const species = await this.db.models.Species.create({});
		const translation = await this.db.models.SpeciesTranslation.create({
			language: speciesData.language,
			name: speciesData.name,
			speciesId: species.id,
		});
		return { species, translation };
	}
}
