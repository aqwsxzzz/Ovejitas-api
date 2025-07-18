import { FastifyInstance } from 'fastify';
import * as authController from '../../controllers/v1/auth-controller';
import { authSignUpSchema, authLoginSchema } from '../../schemas/auth-schema';
import { authSignUpResponseSchema, authLoginResponseSchema } from '../../serializers/auth-serializer';
import { userResponseSchema } from '../../serializers/user-serializer';

export default async function authRoutes(fastify: FastifyInstance) {
	fastify.post('/auth/signup', { schema: { body: authSignUpSchema, response: { 200: authSignUpResponseSchema } } }, authController.signUp);
	fastify.post('/auth/login', { schema: { body: authLoginSchema, response: { 200: authLoginResponseSchema } } }, authController.login);
	fastify.get('/auth/me', { preHandler: [fastify.authenticate], schema: { response: { 200: userResponseSchema } } }, authController.getCurrentUser);
	fastify.post('/auth/logout', authController.logout);
}
