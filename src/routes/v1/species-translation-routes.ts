import { FastifyInstance } from "fastify";
import { createSpecieTranslationSchema, deleteSpecieTranslationSchema } from "../../serializers/species-translation-serializer";
import * as speciesTranslationController from "../../controllers/v1/species-translation-controller";
import { SpeciesTranslationIdParams } from "../../types/species-translation-types";

export default async function speciesTranslationRoutes(fastify: FastifyInstance) {
	fastify.post(
		"/species-translation",
		{
			preHandler: [fastify.authenticate],
			schema: {
				body: createSpecieTranslationSchema,
				response: { 201: createSpecieTranslationSchema },
			},
		},
		speciesTranslationController.createSpecieTranslation
	);

	fastify.delete<{ Params: SpeciesTranslationIdParams }>(
		"/species-translation/:translationId",
		{
			preHandler: [fastify.authenticate],
			schema: {
				params: deleteSpecieTranslationSchema,
			},
		},
		speciesTranslationController.deleteSpecieTranslation
	);
}
