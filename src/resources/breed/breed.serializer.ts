import { encodeId } from '../../utils/id-hash-util';
import { BreedModel } from './breed.model';
import { BreedResponse } from './breed.schema';
import { BreedTranslationModel } from '../breed-translation/breed-translation.model';
import { BreedTranslationSerializer } from '../breed-translation/breed-translation.serializer';

type BreedWithTranslations = BreedModel & {
	translations?: BreedTranslationModel[];
};

export class BreedSerializer {
	static serialize(breed: BreedWithTranslations, translations?: BreedTranslationModel[]): BreedResponse {
		const result: BreedResponse = {
			id: encodeId(breed.id),
			speciesId: encodeId(breed.speciesId),
			createdAt: breed.createdAt,
			updatedAt: breed.updatedAt,
		};

		const translationsData = translations ?? breed.translations;
		if (translationsData && translationsData.length > 0) {
			result.translations = BreedTranslationSerializer.serializeMany(translationsData);
		}

		return result;
	}

	static serializeMany(breeds: BreedWithTranslations[]): BreedResponse[] {
		return breeds.map(breed => this.serialize(breed));
	}
}
