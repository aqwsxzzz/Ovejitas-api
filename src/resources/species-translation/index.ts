import { FastifyPluginAsync } from 'fastify';
import speciesTranslationRoutes from './species-translation.routes';

const speciesTranslationPlugin: FastifyPluginAsync = async (fastify) => {
	fastify.register(speciesTranslationRoutes, { prefix: '/species-translations' });
};

export default speciesTranslationPlugin;
