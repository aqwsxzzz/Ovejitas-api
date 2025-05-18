import { Breed } from "../models/breed-model";
import { decodeId } from "../utils/id-hash-util";

export async function findBreedById(breedId: string) {
	const id = decodeId(breedId);
	return await Breed.findByPk(id);
}

export async function findBreedsBySpeciesId(speciesId: string) {
	const id = decodeId(speciesId);
	return await Breed.findAll({ where: { speciesId: id } });
}

export async function isBreedNameUniqueForSpecies(name: string, speciesId: number, excludeId?: number) {
	const where: {
		name: string;
		speciesId: number;
		id?: { $ne: number };
	} = { name, speciesId };

	if (excludeId) where.id = { $ne: excludeId };
	const count = await Breed.count({ where });
	return count === 0;
}
