import { FastifyPluginAsync } from 'fastify';
import weatherRoutes from './weather.routes';

const weatherPlugin: FastifyPluginAsync = async (fastify) => {
	fastify.register(weatherRoutes, { prefix: '/weather' });
};

export default weatherPlugin;
