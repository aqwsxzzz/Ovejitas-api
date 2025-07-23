import { encodeId } from '../../utils/id-hash-util';
import { SpeciesTranslationModel } from './species-translation.model';
import { SpeciesTranslationResponse } from './species-translation.schema';

export class SpeciesSerializer {
	static serialize(speciesTranslation: SpeciesTranslationModel): SpeciesTranslationResponse {
		return {
			id: encodeId(speciesTranslation.dataValues.id),
			speciesId: encodeId(speciesTranslation.dataValues.speciesId),
			language: speciesTranslation.dataValues.language,
			name: speciesTranslation.dataValues.name,
			createdAt: speciesTranslation.dataValues.createdAt,
			updatedAt: speciesTranslation.dataValues.updatedAt,
		};
	}

	static serializeMany(speciesTranslations: SpeciesTranslationModel[]): SpeciesTranslationResponse[] {
		return speciesTranslations.map(speciesTranslation => this.serialize(speciesTranslation));
	}
}
