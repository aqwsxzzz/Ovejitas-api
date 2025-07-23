import { FastifyReply, FastifyRequest } from 'fastify';
import { Species } from '../../models/species-model';
import { IGetSpeciesByIdQuery, ISpeciesIdParam, SpeciesCreateRoute, SpeciesListParams } from '../../types/species-types';
import { serializeSpecies } from '../../serializers/species-serializer';
import { decodeId } from '../../utils/id-hash-util';
import { SpeciesTranslation } from '../../models/species-translation-model';
import { findAllSpeciesWithTranslation, findSpeciesWithTranslationById } from '../../utils/species-util';

export const createSpecies = async (request: FastifyRequest<SpeciesCreateRoute>, reply: FastifyReply) => {
	const { name, languageCode } = request.body;
	const sequelize = request.server.sequelize;
	let speciesWithTranslation: (Species & { translations: SpeciesTranslation[] }) | null = null;
	let translation: SpeciesTranslation | undefined = undefined;

	try {
		await sequelize.transaction(async (t) => {
			const species = await Species.create({}, { transaction: t });

			await SpeciesTranslation.create(
				{
					speciesId: species.id,
					languageCode,
					name,
				},
				{ transaction: t },
			);

			speciesWithTranslation = (await Species.findByPk(species.id, {
				include: [{ model: SpeciesTranslation, where: { languageCode }, as: 'translations' }],
				transaction: t,
			})) as (Species & { translations: SpeciesTranslation[] }) | null;

			if (!speciesWithTranslation || !speciesWithTranslation.translations || speciesWithTranslation.translations.length === 0) {
				throw new Error('Failed to create species with translation');
			}
			translation = speciesWithTranslation.translations[0];
		});
	} catch (error) {
		return reply.code(500).send({ message: 'Failed to create species and translation', error: error instanceof Error ? error.message : error });
	}

	if (!speciesWithTranslation || !translation) {
		return reply.code(500).send({ message: 'Failed to create species and translation' });
	}

	reply.code(201).send(serializeSpecies(speciesWithTranslation, translation));
};

export const getSpecies = async (request: FastifyRequest<{ Querystring: SpeciesListParams }>, reply: FastifyReply) => {
	const languageCode = request.query.language;
	if (!languageCode) {
		return reply.code(400).send({ message: 'Language not specified' });
	}
	const speciesList = await findAllSpeciesWithTranslation(languageCode);

	const speciesListWithTranslation = speciesList
		.map((species) => {
			const translation = species.translations[0];
			return translation ? serializeSpecies(species, translation) : null;
		})
		.filter(Boolean);

	if (!speciesListWithTranslation || speciesListWithTranslation.length === 0) {
		return reply.code(404).send({ message: 'No species found in the requested language' });
	}

	reply.send(speciesListWithTranslation);
};

export const getSpeciesById = async (request: FastifyRequest<{ Params: ISpeciesIdParam; Querystring: IGetSpeciesByIdQuery }>, reply: FastifyReply) => {
	const languageCode = request.query.language;
	if (!languageCode) {
		return reply.code(400).send({ message: 'Language not specified' });
	}
	const { id } = request.params;
	const species = await findSpeciesWithTranslationById(id, languageCode);
	if (!species) {
		return reply.code(404).send({ message: 'Species not found' });
	}
	const translation = (species as Species & { translations: SpeciesTranslation[] }).translations?.[0];
	if (!translation) {
		return reply.code(404).send({ message: `No translation found for species in language '${languageCode}'` });
	}
	reply.send(serializeSpecies(species, translation));
};

export const deleteSpecies = async (request: FastifyRequest<{ Params: ISpeciesIdParam }>, reply: FastifyReply) => {
	const { id } = request.params;
	const species = await Species.findByPk(decodeId(id));
	if (!species) {
		return reply.code(404).send({ message: 'Species not found' });
	}
	await species.destroy();
	reply.send({ message: 'Species deleted' });
};
