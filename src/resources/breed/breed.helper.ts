import { Database } from '../../database';

export async function isBreedNameUniqueForSpecies(name: string, speciesId: number, db: Database) {
	const where: {
        name: string;
        speciesId: number;
        id?: { $ne: number };
    } = { name, speciesId };

	const count = await db.models.Breed.count({ where });
	return count === 0;
}
