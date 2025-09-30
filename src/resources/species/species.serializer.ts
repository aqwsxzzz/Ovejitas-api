import { encodeId } from '../../utils/id-hash-util';
import { SpeciesTranslationModel } from '../species-translation/species-translation.model';
import { SpeciesModel } from './species.model';
import { SpeciesResponse } from './species.schema';

export class SpeciesSerializer {
	static serialize(species: SpeciesModel & { translations?: SpeciesTranslationModel[] }): SpeciesResponse {
		if (!species.translations) {
			return {
				id: encodeId(species.id),
				createdAt: species.createdAt,
				updatedAt: species.updatedAt,
			};
		}

		return {
			id: encodeId(species.id),
			createdAt: species.createdAt,
			updatedAt: species.updatedAt,
			translations: species.translations.map(t => ({
				id: encodeId(t.id),
				language: t.language,
				name: t.name,
				createdAt: t.createdAt,
				updatedAt: t.updatedAt,
			})),
		};
	}

	static serializeMany(species: SpeciesModel[]): SpeciesResponse[] {
		return species.map(s => this.serialize(s));
	}

}
