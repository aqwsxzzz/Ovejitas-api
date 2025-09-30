import fp from 'fastify-plugin';
import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import jwt from 'jsonwebtoken';
import { UserModel } from '../resources/user/user.model';
import { UserRole } from '../resources/user/user.schema';
import { FarmMemberRole } from '../resources/farm-member/farm-member.schema';
import { createAuthorizeDecorator } from '../utils/rbac';

const JWT_SECRET = process.env.JWT_SECRET || 'your_jwt_secret';

interface JWTPayload {
	id: number;
	email: string;
	role: UserRole;
	farmRole: FarmMemberRole;
}

export default fp(async function authenticationPlugin(fastify: FastifyInstance) {
	fastify.decorate('authenticate', async function (request: FastifyRequest, reply: FastifyReply) {
		const token = request.cookies.jwt;
		if (!token) {
			reply.error('Access denied', 401);
			return;
		}

		try {
			const decoded = jwt.verify(token, JWT_SECRET) as JWTPayload;
			request.user = {
				id: decoded.id,
				email: decoded.email,
				role: decoded.role,
				farmRole: decoded.farmRole,
			};

			// Fetch user from DB to get lastVisitedFarmId and language
			const user = await UserModel.findByPk(decoded.id);
			if (!user || typeof user.dataValues.lastVisitedFarmId !== 'number') {
				reply.error('Access denied', 401);
				return;
			}
			request.lastVisitedFarmId = user.dataValues.lastVisitedFarmId;
			request.language = user.dataValues.language || 'en';
		} catch (err) {
			console.error('Authentication error:', err);
			reply.error('Access denied', 401);
			return;
		}
	});

	// Register the authorize decorator
	fastify.decorate('authorize', createAuthorizeDecorator(fastify));
});
