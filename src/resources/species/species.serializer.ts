import { encodeId } from '../../utils/id-hash-util';
import { SpeciesTranslationModel } from '../species-translation/species-translation.model';
import { SpeciesModel } from './species.model';
import { SpeciesResponse } from './species.schema';

export class SpeciesSerializer {
	static serialize(species: SpeciesModel, translation: SpeciesTranslationModel): SpeciesResponse {
		return {
			id: encodeId(species.id),
			createdAt: species.createdAt,
			updatedAt: species.updatedAt,
			translationId: encodeId(translation.id),
		};
	}
}
