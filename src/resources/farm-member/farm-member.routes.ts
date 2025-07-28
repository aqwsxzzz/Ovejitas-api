import { FastifyPluginAsync, FastifyRequest } from 'fastify';
import { createFarmMemberSchema, FarmMemberCreateInput } from './farm-member.schema';

const farmMemberRoutes: FastifyPluginAsync = async (fastify) => {
	fastify.post('/', {
		schema: createFarmMemberSchema,
		preHandler: fastify.authenticate,
	}, async (request: FastifyRequest<{ Body: FarmMemberCreateInput }>, reply) => {
		try {
			const { role, farmId, userId } = request.body;
			const farmMember = await fastify.farmMemberService.createFarmMember({ role, farmId, userId });
			reply.status(201).send(farmMember);
		} catch (error) {
			fastify.handleDbError(error, reply);
		}
	});
};

export default farmMemberRoutes;
