import { FastifyReply, FastifyRequest } from "fastify";
import { Animal } from "../../models/animal-model";
import { serializeAnimal } from "../../serializers/animal-serializer";
import { decodeId } from "../../utils/id-hash-util";
import { findAnimalById, findAnimalsByFarmId, isTagNumberUniqueForFarm } from "../../utils/animal-util";
import { AnimalCreateRoute, AnimalUpdateRoute, AnimalGetRoute, AnimalDeleteRoute, AnimalListRoute, AnimalListByFarmRoute } from "../../types/animal-types";
import { findBreedById } from "../../utils/breed-util";

export const createAnimal = async (request: FastifyRequest<AnimalCreateRoute>, reply: FastifyReply) => {
	const { speciesId, breedId, name, tagNumber, sex, birthDate, weight, status, reproductiveStatus, parentId, motherId, acquisitionType, acquisitionDate } = request.body;
	const { farmId } = request.params;
	const farmIdDecoded = decodeId(farmId)!;
	const speciesIdDecoded = decodeId(speciesId)!;
	const breedIdDecoded = breedId ? decodeId(breedId) : null;
	const parentIdDecoded = parentId ? decodeId(parentId) : null;
	const motherIdDecoded = motherId ? decodeId(motherId) : null;

	// Validate breed-species match
	if (breedId) {
		const breed = await findBreedById(breedId);
		if (!breed) {
			return reply.code(400).send({ message: "Breed not found." });
		}
		if (breed.speciesId !== speciesIdDecoded) {
			return reply.code(400).send({ message: "Selected breed does not belong to the specified species. Please select a valid breed for this species." });
		}
	}

	// Check tag number uniqueness
	if (tagNumber) {
		const isUnique = await isTagNumberUniqueForFarm(tagNumber, farmIdDecoded);
		if (!isUnique) {
			return reply.code(409).send({ message: "Tag number must be unique per farm." });
		}
	}
	const animal = await Animal.create({
		farmId: farmIdDecoded,
		speciesId: speciesIdDecoded,
		breedId: breedIdDecoded,
		name,
		tagNumber: tagNumber ?? null,
		sex,
		birthDate: new Date(birthDate),
		weight: weight ?? null,
		status,
		reproductiveStatus,
		parentId: parentIdDecoded,
		motherId: motherIdDecoded,
		acquisitionType,
		acquisitionDate: new Date(acquisitionDate),
	});
	reply.code(201).send(serializeAnimal(animal));
};

export const listAnimalsByFarm = async (request: FastifyRequest<AnimalListByFarmRoute>, reply: FastifyReply) => {
	const { farmId } = request.params;
	if (!farmId) {
		return reply.code(400).send({ message: "farmId is required" });
	}
	const animals = await findAnimalsByFarmId(farmId);
	reply.send(animals.map(serializeAnimal));
};

export const getAnimalById = async (request: FastifyRequest<AnimalGetRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const animal = await findAnimalById(id);
	if (!animal) {
		return reply.code(404).send({ message: "Animal not found" });
	}
	reply.send(serializeAnimal(animal));
};

export const updateAnimal = async (request: FastifyRequest<AnimalUpdateRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const animal = await findAnimalById(id);
	if (!animal) {
		return reply.code(404).send({ message: "Animal not found" });
	}
	const { speciesId, breedId, name, tagNumber, sex, birthDate, weight, status, reproductiveStatus, parentId, motherId, acquisitionType, acquisitionDate } = request.body;
	const { farmId } = request.params;
	if (tagNumber) {
		const isUnique = await isTagNumberUniqueForFarm(tagNumber, farmId ? decodeId(farmId)! : animal.farmId, animal.id);
		if (!isUnique) {
			return reply.code(409).send({ message: "Tag number must be unique per farm." });
		}
	}
	if (farmId) animal.set("farmId", decodeId(farmId)!);
	if (speciesId) animal.set("speciesId", decodeId(speciesId)!);
	if (breedId !== undefined) animal.set("breedId", breedId ? decodeId(breedId) : null);
	if (name) animal.set("name", name);
	if (tagNumber !== undefined) animal.set("tagNumber", tagNumber ?? null);
	if (sex) animal.set("sex", sex);
	if (birthDate) animal.set("birthDate", new Date(birthDate));
	if (weight !== undefined) animal.set("weight", weight ?? null);
	if (status) animal.set("status", status);
	if (reproductiveStatus) animal.set("reproductiveStatus", reproductiveStatus);
	if (parentId !== undefined) animal.set("parentId", parentId ? decodeId(parentId) : null);
	if (motherId !== undefined) animal.set("motherId", motherId ? decodeId(motherId) : null);
	if (acquisitionType) animal.set("acquisitionType", acquisitionType);
	if (acquisitionDate) animal.set("acquisitionDate", new Date(acquisitionDate));

	await animal.save();

	reply.send(serializeAnimal(animal));
};

export const deleteAnimal = async (request: FastifyRequest<AnimalDeleteRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const animal = await findAnimalById(id);
	if (!animal) {
		return reply.code(404).send({ message: "Animal not found" });
	}
	await animal.destroy();
	reply.send({ message: "Animal deleted (soft)" });
};
