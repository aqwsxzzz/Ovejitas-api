
import { FastifyPluginAsync } from 'fastify';
import { authSchemas, loginUserSchema, signupUserSchema, UserLoginInput, UserSignupInput } from './auth.schema';
import { UserSerializer } from '../user/user.serializer';
import { AuthService } from './auth.service';
import { User, UserParamsSchema } from '../user/user.schema';
import { decodeId } from '../../utils/id-hash-util';

const authPlugin: FastifyPluginAsync = async (fastify) => {
	authSchemas.forEach(schema => fastify.addSchema(schema));

	const authService = new AuthService(fastify.db);

	fastify.decorate('authService', authService);

	fastify.post('/auth/login', { schema: loginUserSchema }, async (request, reply) => {
		try {
			const { email, password } = request.body as UserLoginInput;
			const { user, token } = await fastify.authService.login({ email, password });

			reply.setCookie('jwt', token, {
				httpOnly: true,
				path: '/',
				sameSite: true,
				secure: process.env.NODE_ENV === 'production',
				maxAge: 60 * 60 * 24, // 1 day
			}).success(UserSerializer.serialize(user), 'Login successful');

		} catch (error) {
			console.log('🚀 ~ fastify.post ~ error:', error);
			fastify.handleDbError(error, reply);
		}
	});

	fastify.post('/auth/signup', { schema: signupUserSchema }, async (request, reply) => {
		try {
			const { email, password, displayName, invitationToken, language } = request.body as UserSignupInput;
			const { user, message } = await fastify.authService.signup({ email, password, displayName, invitationToken, language });
			reply.success(UserSerializer.serialize(user), message);
		} catch (error) {
			console.log('🚀 ~ fastify.post ~ error:', error);
			fastify.handleDbError(error, reply);
		}
	});

	fastify.post('/auth/logout', { preHandler: fastify.authenticate }, async (request, reply) => {
		try {
			reply.clearCookie('jwt', { path: '/' });
			reply.success('Logged out');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/auth/me', { preHandler: fastify.authenticate }, async (request, reply) => {
		try {
			const { id } = request.user as User;
			const user = await fastify.authService.getCurrentUser(id);
			reply.success(UserSerializer.serialize(user));
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default authPlugin;
