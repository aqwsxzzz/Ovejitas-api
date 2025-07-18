import { FastifyInstance, FastifyPluginAsync } from 'fastify';
import { updateUserSchema, UserParamsSchema, userSchemas, UserUpdateInput } from './user.schema';
import { UserSerializer } from './user.serializer';
import { UserService } from './user.service';
import { decodeId } from '../../utils/id-hash-util';

const userPlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {

	userSchemas.forEach(schema => fastify.addSchema(schema));

	const userSerivce = new UserService(fastify.db);

	fastify.decorate('userService', userSerivce);

	fastify.put('/users/:id', { schema: updateUserSchema, preHandler: fastify.authenticate }, async (request, reply) => {
		try {
			const userId = request.params as UserParamsSchema;
			const userData = request.body as UserUpdateInput;
			const updatedUser = await fastify.userService.updateUser(decodeId(userId!.id!)!, userData);
			if (!updatedUser) {
				return reply.error('User not found', 404);
			}
			const serializedUser = UserSerializer.serialize(updatedUser);
			reply.success(serializedUser);
		} catch (error) {
			console.log('🚀 ~ fastify.put ~ error:', error);
			fastify.handleDbError(error, reply);
		}
	});

	fastify.delete('/users/:id', { preHandler: fastify.authenticate }, async (request, reply) => {
		try {
			const userId = request.params as UserParamsSchema;
			await fastify.userService.deleteUser(decodeId(userId!.id!)!);
			reply.success(null, 'User deleted successfully');
		} catch (error) {
			console.log('🚀 ~ fastify.delete ~ error:', error);
			fastify.handleDbError(error, reply);
		}

	});

};

export default userPlugin;
