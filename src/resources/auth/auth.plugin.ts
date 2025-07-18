import { FastifyPluginAsync } from 'fastify';
import { authSchemas, loginUserSchema, UserLoginInput } from './auth.schema';
import { UserSerializer } from '../user/user.serializer';
import { AuthService } from './auth.service';

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

	fastify.post('/auth/logout', async (request, reply) => {
		try {
			await fastify.authService.logout(request, reply);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/auth/me', { preHandler: fastify.authenticate }, async (request, reply) => {
		try {
			const user = await fastify.authService.currentUser(request);
			reply.success(UserSerializer.serialize(user));
		} catch (error) {
			console.log('🚀 ~ fastify.get ~ error:', error);
			fastify.handleDbError(error, reply);
		}
	});
};

export default authPlugin;
