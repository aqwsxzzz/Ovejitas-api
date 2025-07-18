import { FastifyPluginAsync } from 'fastify';
import { createFarmMemberSchema, FarmMemberCreateInput, farmMemberSchemas  } from './farm-member.schema';
import { FarmMemberService } from './farm-member.service';

const farmMemberPlugin: FastifyPluginAsync = async (fastify) => {
	farmMemberSchemas.forEach(schema => fastify.addSchema(schema));

	const farmMemberService = new FarmMemberService(fastify.db);

	fastify.decorate('farmMemberService', farmMemberService);

	fastify.post('/farm-members', { schema: createFarmMemberSchema, preHandler: fastify.authenticate }, async (request, reply) => {
		const { role, farmId, userId } = request.body as FarmMemberCreateInput;
		const farmMember = await fastify.farmMemberService.createFarmMember({ role, farmId, userId });
		reply.status(201).send(farmMember);
	});

};

export default farmMemberPlugin;
