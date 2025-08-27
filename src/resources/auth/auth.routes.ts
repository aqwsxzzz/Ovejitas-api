import { FastifyPluginAsync, FastifyRequest } from 'fastify';
import { loginUserSchema, signupUserSchema, UserLoginInput, UserSignupInput } from './auth.schema';
import { UserSerializer } from '../user/user.serializer';

const cookieObj: {
	httpOnly: boolean;
	sameSite: 'strict' | 'lax' | 'none';
	secure: boolean;
	maxAge: number;
	path: string;
	domain: string | undefined;
} = { httpOnly: true,
	sameSite: process.env.NODE_ENV === 'development' ? 'strict' : 'none',
	secure: process.env.NODE_ENV !== 'development',
	maxAge: 60 * 60 * 24, // 1 day
	path: '/',
	domain: process.env.COOKIE_DOMAIN || undefined };

const authRoutes: FastifyPluginAsync = async (fastify) => {
	// Routes now use the decorated service instead of creating a new instance

	fastify.post(
		'/login',
		{ schema: loginUserSchema },
		async (request: FastifyRequest<{ Body: UserLoginInput }>, reply) => {
			try {
				const { email, password } = request.body;
				const { user, token } = await fastify.authService.login({ email, password });

				reply
					.setCookie('jwt', token, cookieObj)
					.success(UserSerializer.serialize(user), 'Login successful');
			} catch (error) {
				fastify.handleDbError(error, reply);
			}
		},
	);

	fastify.post(
		'/signup',
		{ schema: signupUserSchema },
		async (request: FastifyRequest<{ Body: UserSignupInput }>, reply) => {
			try {
				const { email, password, displayName, invitationToken, language } = request.body;
				const { user, message } = await fastify.authService.signup({
					email,
					password,
					displayName,
					invitationToken,
					language,
				});
				reply.success(UserSerializer.serialize(user), message);
			} catch (error) {
				fastify.handleDbError(error, reply);
			}
		},
	);

	fastify.post('/logout', { preHandler: fastify.authenticate }, async (_request, reply) => {
		try {
			reply.clearCookie('jwt', cookieObj);
			reply.success('Logged out');
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.get('/me', { preHandler: fastify.authenticate }, async (request: FastifyRequest, reply) => {
		try {
			const { id } = request.user!;
			const user = await fastify.authService.getCurrentUser(id);
			reply.success(UserSerializer.serialize(user));
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default authRoutes;
