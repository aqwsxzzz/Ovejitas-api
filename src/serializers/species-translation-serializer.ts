import { SpeciesTranslation } from "../models/species-translation-model";
import { encodeId } from "../utils/id-hash-util";

export const serializeSpecieTranslation = (translation: SpeciesTranslation) => {
	return {
		id: encodeId(translation.id),
		speciesId: encodeId(translation.speciesId),
		languageCode: translation.languageCode,
		name: translation.name,
	};
};
