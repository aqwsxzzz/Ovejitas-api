import { FastifyInstance } from "fastify";
import { speciesTranslationCreateSchema, speciesTranslationDeleteSchema } from "../../schemas/species-translation-schema";
import * as speciesTranslationController from "../../controllers/v1/species-translation-controller";
import { SpeciesTranslationIdParams } from "../../types/species-translation-types";

export default async function speciesTranslationRoutes(fastify: FastifyInstance) {
	fastify.post(
		"/species-translation",
		{
			preHandler: [fastify.authenticate],
			schema: {
				body: speciesTranslationCreateSchema,
				response: { 201: speciesTranslationCreateSchema },
			},
		},
		speciesTranslationController.createSpecieTranslation
	);

	fastify.delete<{ Params: SpeciesTranslationIdParams }>(
		"/species-translation/:translationId",
		{
			preHandler: [fastify.authenticate],
			schema: {
				params: speciesTranslationDeleteSchema,
			},
		},
		speciesTranslationController.deleteSpecieTranslation
	);
}
