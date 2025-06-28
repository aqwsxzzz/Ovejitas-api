import { FastifyReply, FastifyRequest } from "fastify";
import { Breed } from "../../models/breed-model";
import { serializeBreed } from "../../serializers/breed-serializer";
import { decodeId } from "../../utils/id-hash-util";
import { findBreedById, findBreedsBySpeciesId, isBreedNameUniqueForSpecies } from "../../utils/breed-util";
import { BreedCreateRoute, BreedUpdateRoute, BreedGetRoute, BreedDeleteRoute, BreedListRoute } from "../../types/breed-types";

export const createBreed = async (request: FastifyRequest<BreedCreateRoute>, reply: FastifyReply) => {
	const { speciesId, name } = request.body;
	const speciesIdDecoded = decodeId(speciesId)!;
	// Check uniqueness
	const isUnique = await isBreedNameUniqueForSpecies(name, speciesIdDecoded);
	if (!isUnique) {
		return reply.code(409).send({ message: "Breed name must be unique per species." });
	}
	const breed = await Breed.create({ speciesId: speciesIdDecoded, name });
	reply.code(201).send(serializeBreed(breed));
};

export const listBreeds = async (request: FastifyRequest<BreedListRoute>, reply: FastifyReply) => {
	const { speciesId } = request.query;
	let breeds;
	if (speciesId) {
		breeds = await findBreedsBySpeciesId(speciesId);
	} else {
		breeds = await Breed.findAll();
	}
	reply.send(breeds.map(serializeBreed));
};

export const getBreedById = async (request: FastifyRequest<BreedGetRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const breed = await findBreedById(id);
	if (!breed) {
		return reply.code(404).send({ message: "Breed not found" });
	}
	reply.send(serializeBreed(breed));
};

export const updateBreed = async (request: FastifyRequest<BreedUpdateRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const { name, speciesId } = request.body;
	const breed = await findBreedById(id);
	if (!breed) {
		return reply.code(404).send({ message: "Breed not found" });
	}
	if (name || speciesId) {
		const newSpeciesId = speciesId ? decodeId(speciesId)! : breed.speciesId;
		const newName = name || breed.name;
		const isUnique = await isBreedNameUniqueForSpecies(newName, newSpeciesId, breed.id);
		if (!isUnique) {
			return reply.code(409).send({ message: "Breed name must be unique per species." });
		}
		breed.set("name", newName);
		breed.set("speciesId", newSpeciesId);
		await breed.save();
	}
	reply.send(serializeBreed(breed));
};

export const deleteBreed = async (request: FastifyRequest<BreedDeleteRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const breed = await findBreedById(id);
	if (!breed) {
		return reply.code(404).send({ message: "Breed not found" });
	}
	await breed.destroy();
	reply.send({ message: "Breed deleted" });
};
