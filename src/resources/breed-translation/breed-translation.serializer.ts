import { encodeId } from '../../utils/id-hash-util';
import { BreedTranslationModel } from './breed-translation.model';
import { BreedTranslationResponse } from './breed-translation.schema';

export class BreedTranslationSerializer {
	static serialize(breedTranslation: BreedTranslationModel): BreedTranslationResponse {
		return {
			id: encodeId(breedTranslation.id),
			breedId: encodeId(breedTranslation.breedId),
			language: breedTranslation.language,
			name: breedTranslation.name,
			createdAt: breedTranslation.createdAt,
			updatedAt: breedTranslation.updatedAt,
		};
	}

	static serializeMany(breedTranslations: BreedTranslationModel[]): BreedTranslationResponse[] {
		return breedTranslations.map(breedTranslation => this.serialize(breedTranslation));
	}
}
