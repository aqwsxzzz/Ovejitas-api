import { FastifyPluginAsync } from 'fastify';
import breedTranslationRoutes from './breed-translation.routes';

const breedTranslationPlugin: FastifyPluginAsync = async (fastify) => {
	fastify.register(breedTranslationRoutes, { prefix: '/breed-translations' });
};

export default breedTranslationPlugin;
