import { Species } from "../models/species-model";
import { SpeciesTranslation } from "../models/species-translation-model";
import { decodeId } from "../utils/id-hash-util";

export async function findSpeciesWithTranslationById(speciesId: string, languageCode: string): Promise<(Species & { translations: SpeciesTranslation[] }) | null> {
	const id = decodeId(speciesId);
	const species = await Species.findByPk(id, {
		include: [
			{
				model: SpeciesTranslation,
				as: "translations",
				where: { languageCode },
				required: false,
			},
		],
	});
	return species as (Species & { translations: SpeciesTranslation[] }) | null;
}

export async function findAllSpeciesWithTranslation(languageCode: string): Promise<(Species & { translations: SpeciesTranslation[] })[]> {
	const result = await Species.findAll({
		include: [
			{
				model: SpeciesTranslation,
				as: "translations",
				where: { languageCode },
				required: false,
			},
		],
	});
	return result as (Species & { translations: SpeciesTranslation[] })[];
}
