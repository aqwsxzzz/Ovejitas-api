import { FastifyPluginAsync, FastifyRequest } from 'fastify';
import {
	deleteUserSchema,
	updateUserSchema,
	UserParams,
	UserUpdateInput,
} from './user.schema';
import { UserSerializer } from './user.serializer';
import { decodeId } from '../../utils/id-hash-util';

const userRoutes: FastifyPluginAsync = async (fastify) => {
	fastify.put('/:id', {
		schema: updateUserSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: UserParams, Body: UserUpdateInput }>, reply) => {
		try {
			const userId = request.params;
			const userData = request.body;
			const updatedUser = await fastify.userService.updateUser(decodeId(userId!.id!)!, userData);
			if (!updatedUser) {
				return reply.error('User not found', 404);
			}
			const serializedUser = UserSerializer.serialize(updatedUser);
			reply.success(serializedUser);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});

	fastify.delete('/:id', {
		schema: deleteUserSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Params: UserParams }>, reply) => {
		try {
			const userId = request.params;
			await fastify.userService.deleteUser(decodeId(userId!.id!)!);
			reply.success(null, 'User deleted successfully');
		} catch (error) {
			console.log('🚀 ~ fastify.delete ~ error:', error);
			fastify.handleDbError(error, reply);
		}
	});
};

export default userRoutes;
