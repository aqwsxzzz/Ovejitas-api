import { encodeId } from '../../utils/id-hash-util';
import { SpeciesTranslationModel } from './species-translation.model';
import { SpeciesTranslationResponse } from './species-translation.schema';

export class SpeciesTranslationSerializer {
	static serialize(speciesTranslation: SpeciesTranslationModel): SpeciesTranslationResponse {
		return {
			id: encodeId(speciesTranslation.id),
			speciesId: encodeId(speciesTranslation.speciesId),
			language: speciesTranslation.language,
			name: speciesTranslation.name,
			createdAt: speciesTranslation.createdAt,
			updatedAt: speciesTranslation.updatedAt,
		};
	}

	static serializeMany(speciesTranslations: SpeciesTranslationModel[]): SpeciesTranslationResponse[] {
		return speciesTranslations.map(speciesTranslation => this.serialize(speciesTranslation));
	}
}
