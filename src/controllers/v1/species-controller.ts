import { FastifyReply, FastifyRequest, RouteGenericInterface } from "fastify";
import { Species } from "../../models/species-model";
import { ISpeciesUpdateBody, ISpeciesUpdateParams, ISpeciesDeleteParams } from "../../types/species-types";
import { serializeSpecies } from "../../serializers/species-serializer";
import { decodeId } from "../../utils/id-hash-util";
export interface SpeciesUpdateRoute extends RouteGenericInterface {
	Params: ISpeciesUpdateParams;
	Body: ISpeciesUpdateBody;
}

export const createSpecies = async (request: FastifyRequest, reply: FastifyReply) => {
	const { name } = request.body as { name: string };
	const species = await Species.create({ name });
	reply.code(201).send(serializeSpecies(species));
};

export const getSpecies = async (request: FastifyRequest, reply: FastifyReply) => {
	const speciesList = await Species.findAll();
	reply.send(speciesList.map(serializeSpecies));
};

export const updateSpecies = async (request: FastifyRequest<SpeciesUpdateRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const { name } = request.body;
	const species = await Species.findByPk(decodeId(id));
	if (!species) {
		return reply.code(404).send({ message: "Species not found" });
	}
	species.set({ name });
	await species.save();
	reply.send(serializeSpecies(species));
};

export interface SpeciesDeleteRoute extends RouteGenericInterface {
	Params: ISpeciesDeleteParams;
}

export const deleteSpecies = async (request: FastifyRequest<SpeciesDeleteRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const species = await Species.findByPk(decodeId(id));
	if (!species) {
		return reply.code(404).send({ message: "Species not found" });
	}
	await species.destroy();
	reply.send({ message: "Species deleted" });
};
