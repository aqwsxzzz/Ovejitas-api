import fp from 'fastify-plugin';
import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import jwt from 'jsonwebtoken';
import { UserModel } from '../resources/user/user.model';

const JWT_SECRET = process.env.JWT_SECRET || 'your_jwt_secret';

export default fp(async function authenticationPlugin(fastify: FastifyInstance) {
	fastify.decorate('authenticate', async function (request: FastifyRequest, reply: FastifyReply) {
		const token = request.cookies.jwt;
		if (!token) {
			reply.error('Access denied', 401);
			return;
		}

		try {
			const decoded = jwt.verify(token, JWT_SECRET) as { id: number; email: string; role: string };
			request.user = decoded;

			// Fetch user from DB to get lastVisitedFarmId and language
			const user = await UserModel.findByPk(decoded.id);
			if (!user || typeof user.get('lastVisitedFarmId') !== 'number') {
				reply.error('Access denied', 401);
				return;
			}
			request.lastVisitedFarmId = user.get('lastVisitedFarmId') as number;
			request.language = user.get('language') as 'en' | 'es' || 'en';
		} catch (err) {
			console.error('Authentication error:', err);
			reply.error('Access denied', 401);
			return;
		}
	});
});
