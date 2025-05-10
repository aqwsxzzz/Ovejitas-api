import { FastifyReply } from "fastify";

import { FastifyRequest } from "fastify";
import { Species } from "../../models/species-model";
import { ICreateSpecieBody, SpeciesTranslationIdParams } from "../../types/species-translation-types";
import { SpeciesTranslation } from "../../models/species-translation-model";
import { decodeId } from "../../utils/id-hash-util";
import { serializeSpecieTranslation } from "../../serializers/species-translation-serializer";

export const createSpecieTranslation = async (request: FastifyRequest<ICreateSpecieBody>, reply: FastifyReply) => {
	const { speciesId, languageCode, name } = request.body;
	const species = await Species.findByPk(decodeId(speciesId));
	if (!species) {
		return reply.code(404).send({ message: "Species not found" });
	}

	const translation = await SpeciesTranslation.create({
		speciesId: decodeId(speciesId)!,
		languageCode,
		name,
	});

	reply.code(201).send(serializeSpecieTranslation(translation));
};

export const deleteSpecieTranslation = async (request: FastifyRequest<{ Params: SpeciesTranslationIdParams }>, reply: FastifyReply) => {
	const { translationId } = request.params;
	const translation = await SpeciesTranslation.findByPk(decodeId(translationId));
	if (!translation) {
		return reply.code(404).send({ message: "Translation not found" });
	}

	await translation.destroy();

	reply.code(204).send();
};
