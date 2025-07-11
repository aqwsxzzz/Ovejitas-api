import { Op } from "sequelize";
import { Animal } from "../models/animal-model";
import { decodeId } from "../utils/id-hash-util";
import { Species } from "../models/species-model";
import { Breed } from "../models/breed-model";
import { SpeciesTranslation } from "../models/species-translation-model";

export async function findAnimalById(animalId: string) {
    const id = decodeId(animalId);
    return await Animal.findByPk(id, {
        include: [
            {
                model: Species,
                as: "species",
                include: [
                    {
                        model: SpeciesTranslation,
                        as: "translations",
                        required: false,
                    },
                ],
            },
            {
                model: Breed,
                as: "breed",
                required: false,
            },
        ],
    });
}

export async function findAnimalsByFarmId(farmId: string) {
    const id = decodeId(farmId);
    return await Animal.findAll({
        where: { farmId: id },
        include: [
            {
                model: Species,
                as: "species",
                include: [
                    {
                        model: SpeciesTranslation,
                        as: "translations",
                        required: false,
                    },
                ],
            },
            {
                model: Breed,
                as: "breed",
                required: false,
            },
        ],
    });
}

export async function isTagNumberUniqueForFarm(tagNumber: string, farmId: number, speciesId: number, excludeId?: number) {
    if (!tagNumber) return true;
    const where: {
        tagNumber: string;
        farmId: number;
        speciesId: number;
        id?: { [Op.ne]: number };
    } = { tagNumber, farmId, speciesId };

    if (excludeId) where.id = { [Op.ne]: excludeId };
    const count = await Animal.count({ where });

    return count === 0;
}

/**
 * Validates that the selected father is male and the selected mother is female.
 * @param father Animal instance or null
 * @param mother Animal instance or null
 * @returns null if valid, or a user-friendly error message string
 */
export function validateParentSex(father: Animal | null, mother: Animal | null): string | null {
    if (father && father.sex !== "male") {
        return "Selected father must be male.";
    }
    if (mother && mother.sex !== "female") {
        return "Selected mother must be female.";
    }
    return null;
}
