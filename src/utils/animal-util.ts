import { Animal } from "../models/animal-model";
import { decodeId } from "../utils/id-hash-util";

export async function findAnimalById(animalId: string) {
	const id = decodeId(animalId);
	return await Animal.findByPk(id);
}

export async function findAnimalsByFarmId(farmId: string) {
	const id = decodeId(farmId);
	return await Animal.findAll({ where: { farmId: id } });
}

export async function isTagNumberUniqueForFarm(tagNumber: string, farmId: number, excludeId?: number) {
	if (!tagNumber) return true;
	const where: {
		tagNumber: string;
		farmId: number;
		id?: { $ne: number };
	} = { tagNumber, farmId };

	if (excludeId) where.id = { $ne: excludeId };
	const count = await Animal.count({ where });
	return count === 0;
}
